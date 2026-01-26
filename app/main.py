import os
import json
from dotenv import load_dotenv

from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from openai import OpenAI

from app.tools import TOOLS
from app.tool_executor import execute_tool_call
from app.tool_executor import auth_sessions

load_dotenv()
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

def extract_call_fields(call_item):
    """
    Responses output item에서 tool 실행에 필요한 식별자/이름/인자를 꺼낸다.
    - function_call: ResponseFunctionToolCall (call_id, name, arguments)
    - tool_call: (SDK/버전에 따라 필드명이 다를 수 있어 fallback 포함)
    """
    if call_item.type == "function_call":
        return call_item.call_id, call_item.name, call_item.arguments

    if call_item.type == "tool_call":
        # 일반적으로 tool_call_id / id 중 하나가 있음(환경별 대응)
        call_id = getattr(call_item, "tool_call_id", None) or getattr(call_item, "call_id", None) or getattr(call_item, "id", None)
        name = getattr(call_item, "name", None)
        args = getattr(call_item, "arguments", None)
        return call_id, name, args

    raise ValueError(f"Unsupported call type: {call_item.type}")


@app.post("/chat")
def chat(req: ChatRequest, authorization: str | None = Header(default=None)):
    
    session = auth_sessions.get(authorization, {})
    
    if session.get("pending_action") == "delete":
        result = execute_tool_call(
            tool_name="confirm_delete_by_chat",
            arguments={"message":req.message},
            auth_header=authorization
        )
        return JSONResponse(
            content={"reply": result.get("message","")},
            media_type="application/json; charset=utf-8",
        )

    # if session.get("pending_action") == "update" and session.get("pending_update_candidates"):
    #     user_message = req.message.strip()
    #     candidates = session["pending_update_candidates"]

    #     # 1) 사용자 입력에서 번호 추출 (ex: "1번 금액 1800원으로 수정")
    #     import re
    #     m_num = re.search(r"(\d+)번", user_message)
    #     if not m_num:
    #         return JSONResponse(
    #             content={"reply": "수정할 항목 번호를 입력해주세요. 예: 1번 금액 1800원"},
    #             media_type="application/json; charset=utf-8",
    #         )
    #     candidate_index = int(m_num.group(1))

    #     # 2) 수정 내용 추출 (날짜, 금액, 메모)
    #     new_data: dict[str, any] = {}

    #     # 금액
    #     m_amount = re.search(r"(\d+)\s*원", user_message)
    #     if m_amount:
    #         new_data["amount"] = int(m_amount.group(1))

    #     # 날짜
    #     m_date_str = re.search(r"(오늘|어제|내일|\d+일\s*[전후]|\d{4}-\d{2}-\d{2})", user_message)
    #     if m_date_str:
    #         try:
    #             new_data["date"] = parse_human_date(m_date_str.group(1))
    #         except ValueError as e:
    #             return JSONResponse(
    #                 content={"reply": str(e)},
    #                 media_type="application/json; charset=utf-8",
    #             )

    #     # 메모
    #     m_memo = re.search(r"(?:메모|내용|설명)\s*(?:을|를|은|는)?\s*(.+?)(?:으로|로)?\s*수정", user_message)
    #     if m_memo:
    #         new_data["memo"] = m_memo.group(1)

    #     if not new_data:
    #         return JSONResponse(
    #             content={"reply": "수정할 내용을 입력해주세요. (금액/날짜/메모)"},
    #             media_type="application/json; charset=utf-8",
    #         )

    #     # 3) confirm 호출
    #     result = execute_tool_call(
    #         tool_name="update_expense_by_chat_confirm",
    #         arguments={
    #             "candidateIndex": candidate_index,
    #             "newData": new_data
    #         },
    #         auth_header=authorization
    #     )

    #     # confirm 끝났으면 세션 초기화
    #     session.pop("pending_action", None)
    #     session.pop("pending_update_candidates", None)
    #     auth_sessions[authorization] = session

    #     return JSONResponse(
    #         content={"reply": result.get("message", "")},
    #         media_type="application/json; charset=utf-8",
    #     )

    if session.get("pending_action") == "update" and session.get("pending_update_candidates"):
        user_message = req.message.strip()
        candidates = session["pending_update_candidates"]

        # 사용자 입력 전체를 LLM에게 맡겨서 JSON(date, amount, memo) 추출
        prompt_messages = [
            {"role": "system", "content": (
                "사용자의 메시지에서 '번호', '날짜', '금액', '메모' 정보를 JSON으로 추출하세요. "
                "날짜는 반드시 YYYY-MM-DD 형식으로, 금액은 숫자로, 메모는 문자열로. "
                "예: {'candidateIndex': 1, 'newData': {'date':'2026-01-25','amount':1800,'memo':'과자'}}"
            )},
            {"role": "user", "content": user_message},
        ]

        llm_response = client.responses.create(
            model="gpt-5-nano",
            input=prompt_messages,
        )

        try:
            llm_args_text = llm_response.output_text.strip()
            llm_args = json.loads(llm_args_text)
            candidate_index = llm_args.get("candidateIndex")
            new_data = llm_args.get("newData", {})
        except Exception:
            return JSONResponse(
                content={"reply": "메시지에서 수정 정보를 추출할 수 없습니다. 예: 1번 금액 1800원, 날짜 2026-01-25, 메모 과자"},
                media_type="application/json; charset=utf-8",
            )

        # confirm 호출
        result = execute_tool_call(
            tool_name="update_expense_by_chat_confirm",
            arguments={"candidateIndex": candidate_index, "newData": new_data},
            auth_header=authorization
        )

        # 세션 초기화
        session.pop("pending_action", None)
        session.pop("pending_update_candidates", None)
        auth_sessions[authorization] = session

        return JSONResponse(
            content={"reply": result.get("message", "")},
            media_type="application/json; charset=utf-8",
        )

    # Step 1) 모델 호출(툴 포함)
    response = client.responses.create(
        model="gpt-5-nano",
        input=[
            {"role": "system", "content": "항상 한국어로만 답변해. 필요하면 함수(tool)를 호출해서 작업을 수행해."},
            {"role": "user", "content": req.message},
        ],
        tools=TOOLS,
    )

    # 디버그용
    # print("OUTPUT_TYPES_1:", [item.type for item in response.output])
    # print("OUTPUT_TEXT_1:", repr(response.output_text))


    # Step 2) tool call이 있는지 확인
    tool_calls = []
    for item in response.output:
        print("RAW_ITEM:", item.type, item)
        if item.type in ("tool_call", "function_call"):
            tool_calls.append(item)
            print(f'tool_calls:{tool_calls}')
    
    # tool call이 없으면 Step 5로 종료(최종 답변)
    if not tool_calls:
        return JSONResponse(
            content={"reply": response.output_text},
            media_type="application/json; charset=utf-8",
        )

    base_messages = [
        {"role": "system", "content": (
          "항상 한국어로만 답변해. 필요하면 함수(tool)를 호출해서 작업을 수행해."
        #   "삭제/수정처럼 돌이킬 수 없는 작업은 식별자(ID)가 없으면 먼저 확인 질문을 해."
        )},
        {"role": "user", "content": req.message},
    ]

    # 1차 호출의 output(function_call 포함)을 그대로 이어붙임
    followup_input = base_messages + response.output

    # tool 실행 시 auth 전달
    tool_results = []
    for tc in tool_calls:
        call_id, tool_name, args = extract_call_fields(tc)

        # arguments가 문자열이면 JSON 파싱
        if isinstance(args, str):
            args = json.loads(args)

        if not isinstance(args, dict):
            args = {}

        # update용 보정
        if tool_name == "update_expense_by_chat":
            # amount가 1이면 (LLM 기본 쓰레기값) 제거
            if args.get("amount") == 1:
                args.pop("amount")

            # memo가 빈 문자열이면 제거
            if "memo" in args and (args["memo"] is None or args["memo"].strip() == ""):
                args.pop("memo")

        # 기존 로직 유지
        args["message"] = req.message

        result = execute_tool_call(tool_name, args, authorization)

        if "candidates" in result:
            return JSONResponse(
                content={
                    "reply": result.get("message", ""),
                    "candidates": result.get("candidates", [])
                },
                media_type="application/json; charset=utf-8"
            )

        if "items" in result:
            # items를 문자열로 포맷
            formatted = "\n".join([f'{e["date"]} {e["amount"]}원 "{e.get("memo","")}" [{e.get("category","")}]' for e in result["items"]])
            return JSONResponse(
                content={"reply": formatted or "내역이 없습니다."},
                media_type="application/json; charset=utf-8",
            )

        if result.get("message"):
            return JSONResponse(
                content={"reply": result["message"]},
                media_type="application/json; charset=utf-8",
            )

        # tool_results.append({
        #     "type": "function_call_output",
        #     "call_id": call_id,
        #     "output": json.dumps(result, ensure_ascii=False),
        # })

    # # Step 4) tool_result를 붙여서 재호출
    # response2 = client.responses.create(
    #     model="gpt-5-nano",
    #     input=followup_input + tool_results,
    #     tools=TOOLS,
    #     store=False,
    # )

    # # 디버그용
    # # print("OUTPUT_TYPES_2:", [item.type for item in response2.output])
    # # print("OUTPUT_TEXT_2:", repr(response2.output_text))


    # # Step 5) 최종 답변 반환
    # return JSONResponse(
    #     content={"reply": response2.output_text},
    #     media_type="application/json; charset=utf-8",
    # )

from datetime import datetime, timedelta
import re

def parse_human_date(date_str: str) -> str:
    """ '오늘', '어제', '내일', '2일 전', '3일 후' → YYYY-MM-DD """
    today = datetime.today().date()
    date_str = date_str.strip()

    if date_str == "오늘":
        return today.isoformat()
    elif date_str == "어제":
        return (today - timedelta(days=1)).isoformat()
    elif date_str == "내일":
        return (today + timedelta(days=1)).isoformat()
    else:
        m = re.match(r"(\d+)일\s*(전|후)", date_str)
        if m:
            n = int(m.group(1))
            return (today - timedelta(days=n) if m.group(2) == "전" else today + timedelta(days=n)).isoformat()
    # 그냥 YYYY-MM-DD 형식이면 그대로 반환
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return date_str
    except ValueError:
        raise ValueError(f"날짜 형식이 올바르지 않습니다: {date_str}")
