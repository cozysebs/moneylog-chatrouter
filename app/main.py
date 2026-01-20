import os
import json
from dotenv import load_dotenv

from fastapi import FastAPI, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from openai import OpenAI

from app.tools import TOOLS
from app.tool_executor import execute_tool_call

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
          "삭제/수정처럼 돌이킬 수 없는 작업은 식별자(ID)가 없으면 먼저 확인 질문을 해."
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

        result = execute_tool_call(tool_name, args, authorization)

        tool_results.append({
            "type": "function_call_output",
            "call_id": call_id,
            "output": json.dumps(result, ensure_ascii=False),
        })

    # Step 4) tool_result를 붙여서 재호출
    response2 = client.responses.create(
        model="gpt-5-nano",
        input=followup_input + tool_results,
        tools=TOOLS,
        store=False,
    )

    # 디버그용
    # print("OUTPUT_TYPES_2:", [item.type for item in response2.output])
    # print("OUTPUT_TEXT_2:", repr(response2.output_text))


    # Step 5) 최종 답변 반환
    return JSONResponse(
        content={"reply": response2.output_text},
        media_type="application/json; charset=utf-8",
    )