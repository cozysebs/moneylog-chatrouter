# app/tool_executor.py
from __future__ import annotations
from typing import Any, Dict, Optional

from app import backend_api

auth_sessions: Dict[str, Dict[str, Any]] = {}

def execute_tool_call(tool_name: str, arguments: Dict[str, Any], auth_header: Optional[str]) -> Dict[str, Any]:
    """
    모델이 요청한 tool call을 실제 '백엔드 REST API'로 실행하고 결과를 dict로 반환한다.
    auth_header: Backend가 Router로 전달한 "Authorization: Bearer <JWT>" 값
    """

    session_key = auth_header or "anonymous"
    session = auth_sessions.get(session_key, {})

    if tool_name == "confirm_delete_by_chat":
        candidates = session.get("pending_delete_candidates", [])

        user_message = arguments.get("message", "").strip()
        selected_numbers = parse_user_selection(user_message)
        
        # ✅ 취소/아니요 처리
        if any(keyword in user_message for keyword in ["취소", "아니요"]):
            session.pop("pending_action", None)
            session.pop("pending_delete_candidates", None)
            session.pop("pending_tx_type", None)
            auth_sessions[session_key] = session
            return {"ok": True, "message": "삭제가 취소되었습니다."}

        # ✅ "모두" 선택 처리
        if "모두" in user_message or "전부" in user_message:
            selected_numbers = [c["number"] for c in candidates]
        else:
            # 숫자로 선택
            selected_numbers = parse_user_selection(user_message)

        if not selected_numbers:
            session.pop("pending_action", None)
            session.pop("pending_delete_candidates", None)
            session.pop("pending_tx_type", None)
            auth_sessions[session_key] = session
            return {
                "ok": False,
                "message": "삭제에 실패했습니다. 처음부터 다시 시도해주세요."
            }

        selected_indexes = [
            c["number"] for c in candidates
            if c.get("number") in selected_numbers
        ]

        if not selected_indexes:
            return {
                "ok": False,
                "message": "선택한 번호가 후보 목록에 없습니다. 다시 골라주세요. (예: 1번)"
            }

        res = backend_api.confirm_delete_by_chat(
            auth_header=auth_header,
            selected_indexes=selected_indexes
        )

        # 상태 정리
        session.pop("pending_action", None)
        session.pop("pending_delete_candidates", None)
        session.pop("pending_tx_type", None)
        auth_sessions[session_key] = session

        return {"ok": True, "message": "삭제 완료"}
    
    if tool_name == "confirm_delete_income_by_chat":
        candidates = session.get("pending_delete_candidates", [])

        user_message = arguments.get("message", "").strip()
        selected_numbers = parse_user_selection(user_message)

        # 취소 처리
        if any(keyword in user_message for keyword in ["취소", "아니요"]):
            session.pop("pending_action", None)
            session.pop("pending_delete_candidates", None)
            session.pop("pending_tx_type", None)
            auth_sessions[session_key] = session
            return {"ok": True, "message": "수입 삭제가 취소되었습니다."}

        # 모두 선택
        if "모두" in user_message or "전부" in user_message:
            selected_numbers = [c["number"] for c in candidates]
        else:
            selected_numbers = parse_user_selection(user_message)

        if not selected_numbers:
            session.pop("pending_action", None)
            session.pop("pending_delete_candidates", None)
            session.pop("pending_tx_type", None)
            auth_sessions[session_key] = session
            return {
                "ok": False,
                "message": "삭제에 실패했습니다. 처음부터 다시 시도해주세요."
            }

        selected_indexes = [
            c["number"] for c in candidates
            if c.get("number") in selected_numbers
        ]

        if not selected_indexes:
            return {
                "ok": False,
                "message": "선택한 번호가 후보 목록에 없습니다. 다시 골라주세요. (예: 1번)"
            }

        res = backend_api.confirm_delete_income_by_chat(
            auth_header=auth_header,
            selected_indexes=selected_indexes
        )

        session.pop("pending_action", None)
        session.pop("pending_delete_candidates", None)
        session.pop("pending_tx_type", None)
        auth_sessions[session_key] = session

        return {"ok": True, "message": "수입 삭제 완료"}


    if tool_name == "update_expense_by_chat_confirm":
        # 세션에서 후보 목록 가져오기
        candidates = session.get("pending_update_candidates", [])

        # 사용자 입력
        candidate_index = arguments.get("candidateIndex")
        new_data = arguments.get("newData", {})

        user_message = arguments.get("message", "").strip()

        # ✅ 취소/아니요 처리
        if any(keyword in user_message for keyword in ["취소", "아니요"]):
            session.pop("pending_action", None)
            session.pop("pending_delete_candidates", None)
            session.pop("pending_tx_type", None)
            auth_sessions[session_key] = session
            return {"ok": True, "message": "수정이 취소되었습니다."}

        # 후보 번호 없으면 바로 에러
        if candidate_index is None:
            return {"ok": False, "message": "수정할 후보 번호가 없습니다."}

        # 후보 목록에서 선택된 후보 찾기
        candidate = next(
            (c for c in candidates if c["number"] == candidate_index),
            None
        )

        if not candidate:
            return {"ok": False, "message": "선택한 번호가 후보 목록에 없습니다."}

        # 부분 수정: date / amount / memo만 허용
        payload_date = new_data.get("date") or candidate["date"]
        payload_amount = (
            int(new_data["amount"])
            if new_data.get("amount") is not None
            else candidate["amount"]
        )
        payload_memo = new_data.get("memo") or candidate["memo"]

        # ✅ confirm 호출 (Spring Boot DTO 구조에 맞게)
        res = backend_api.confirm_update_by_chat(
            auth_header=auth_header,
            selected_index=candidate_index,
            new_date=payload_date,
            new_amount=payload_amount,
            new_memo=payload_memo
        )

        # 세션 정리
        session.pop("pending_action", None)
        session.pop("pending_update_candidates", None)
        session.pop("pending_tx_type", None)
        auth_sessions[session_key] = session

        return res
    
    if tool_name == "update_income_by_chat_confirm":
        candidates = session.get("pending_update_candidates", [])

        candidate_index = arguments.get("candidateIndex")
        new_data = arguments.get("newData", {})

        user_message = arguments.get("message", "").strip()

        # ✅ 취소/아니요 처리
        if any(keyword in user_message for keyword in ["취소", "아니요"]):
            session.pop("pending_action", None)
            session.pop("pending_delete_candidates", None)
            session.pop("pending_tx_type", None)
            auth_sessions[session_key] = session
            return {"ok": True, "message": "수정이 취소되었습니다."}

        if candidate_index is None:
            return {"ok": False, "message": "수정할 수입 후보 번호가 없습니다."}

        candidate = next(
            (c for c in candidates if c["number"] == candidate_index),
            None
        )

        if not candidate:
            return {"ok": False, "message": "선택한 번호가 후보 목록에 없습니다."}

        payload_date = new_data.get("date") or candidate["date"]
        payload_amount = (
            int(new_data["amount"])
            if new_data.get("amount") is not None
            else candidate["amount"]
        )
        payload_memo = new_data.get("memo") or candidate["memo"]

        res = backend_api.confirm_update_income_by_chat(
            auth_header=auth_header,
            selected_index=candidate_index,
            new_date=payload_date,
            new_amount=payload_amount,
            new_memo=payload_memo,
        )

        session.pop("pending_action", None)
        session.pop("pending_update_candidates", None)
        session.pop("pending_tx_type", None)
        auth_sessions[session_key] = session

        return res




    # transaction-controller (CRUD)
    transaction_tools = {
        "create_expense",
        "create_expense_batch",
        "create_income",
        "create_income_batch",
        "list_expenses",
        "list_incomes",
        "delete_expense",
        "update_expense",
        "delete_expense_by_chat",
        "delete_income_by_chat",
        "update_expense_by_chat",
        "update_income_by_chat",
        "get_expense_summary",
        "get_income_summary",
        "get_top_expense_category",
        "top_expense_weekday_avg",
        "delete_latest_transaction",
        "update_latest_transaction",
    }

    if tool_name == "delete_latest_transaction":
        result = backend_api.delete_latest_transaction(
            auth_header=auth_header
        )

        if not result.get("ok"):
            return result

        return {
            "ok": True,
            "message": "삭제가 완료되었습니다."
        }
    if tool_name == "update_latest_transaction":
        # arguments에서 None 값 제거
        date = arguments.get("date")
        amount = arguments.get("amount")
        memo = arguments.get("memo")

        if not date or date in ["0000-01-01","0000-00-00"]:
            date = None

        if amount == 1:
            amount = None

        # 실제 바꾸고 싶은 값만 payload로 보냄
        result = backend_api.update_latest_transaction(
            auth_header=auth_header,
            date=date if date is not None else None,
            amount=amount if amount is not None else None,
            memo=memo if memo is not None else None,
        )

        if not result.get("ok"):
            return result

        tx = result["transaction"]

        return {
            "ok": True,
            "message": (
                f'{tx["date"]} {tx["amount"]}원 '
                f'"{tx.get("memo", "")}" '
                f'[{tx.get("category", "")}] 수정 완료'
            )
        }

    if tool_name in transaction_tools:
        login_error = require_login(auth_header)
        if login_error:
            return login_error


    if tool_name == "create_expense":
        return backend_api.create_expense(
            auth_header=auth_header,
            date=arguments["date"],
            amount=int(arguments["amount"]),
            category=arguments["category"],
            memo=arguments.get("memo", "")
        )
    if tool_name == "create_expense_batch":
        backend_api.create_expense_batch(
            auth_header=auth_header,
            transactions=arguments["transactions"]
        )
        messages = [
            format_transaction_reply(t)
            for t in arguments["transactions"]
        ]
        return {
            "ok": True,
            "message": "\n".join(messages)
        }
    if tool_name == "create_income":
        return backend_api.create_income(
            auth_header=auth_header,
            date=arguments["date"],
            amount=int(arguments["amount"]),
            category=arguments["category"],
            memo=arguments.get("memo", "")
        )
    if tool_name == "create_income_batch":
        backend_api.create_income_batch(
            auth_header=auth_header,
            transactions=arguments["transactions"]
        )

        messages = [
            format_transaction_reply(t)
            for t in arguments["transactions"]
        ]

        return {
            "ok": True,
            "message": "\n".join(messages)
        }
    if tool_name == "top_expense_weekday_avg":
        data = backend_api.top_expense_weekday_avg(
            auth_header=auth_header,
            scope=arguments["scope"],
            month=arguments.get("month"),
            year=arguments.get("year"),
        )
        weekday = data.get("weekday", "")
        avg = data.get("avgAmount", 0)
        # scope별 안내 문구
        if arguments["scope"] == "month":
            m = arguments.get("month")
            if m:
                # YYYY-MM -> YYYY년 M월
                y, mm = m.split("-")
                period_label = f"{int(y)}년 {int(mm)}월"
            else:
                period_label = "이번 달"
        elif arguments["scope"] == "year":
            y = arguments.get("year")
            period_label = f"{int(y)}년" if y else "올해"
        else:
            period_label = "해당 기간"

        # 원 단위 반올림
        try:
            avg_int = int(round(float(avg)))
        except Exception:
            avg_int = 0

        return {
            "ok": True,
            "message": f'{period_label} 기준 평균 지출이 가장 큰 요일은 {weekday}이고, 평균 {avg_int:,}원입니다.'
        }
    if tool_name == "list_expenses":
        items = backend_api.list_expenses(
            auth_header=auth_header,
            limit=int(arguments.get("limit", 10))
        )
        return {
            "ok" : True,
            "message": "조회 완료",
            "items": items.get("items", [])
        }
    if tool_name == "list_incomes":
        items = backend_api.list_incomes(
            auth_header=auth_header,
            limit=int(arguments.get("limit", 10))
        )
        return {
            "ok": True,
            "message": "수입 조회 완료",
            "items": items.get("items", [])
        }
    if tool_name == "delete_expense":
        return backend_api.delete_expense(
            auth_header=auth_header,
            expense_id=int(arguments["expense_id"])
        )
    if tool_name == "update_expense":
        return backend_api.update_expense(
            auth_header=auth_header,
            expense_id=int(arguments["expense_id"]),
            date=arguments["date"],
            amount=int(arguments["amount"]),
            category=arguments["category"],
            memo=arguments.get("memo", "")
        )
    
    if tool_name == "delete_expense_by_chat":
        result = backend_api.delete_expense_by_chat(
            auth_header=auth_header,
            date=arguments["date"],
            amount=int(arguments.get("amount", 0)),
            memo=arguments.get("memo", "")
        )

        if result.get("status") == 409:
            candidates = result["candidates"]

            # ✅ 컨펌 단계 진입 표시
            session["pending_action"] = "delete"
            session["pending_delete_candidates"] = candidates
            session["pending_tx_type"] = "EXPENSE"
            auth_sessions[session_key] = session

            message = "삭제 가능한 후보가 여러 개 있습니다:\n"
            for c in candidates:
                message += f'{c["number"]}번. {c["date"]} {c["amount"]}원 "{c["memo"]}" [{c["category"]}]\n'
            message += "\n삭제 할 내역의 번호를 말해주세요. 모두 삭제를 원하시면 모두 삭제 또는 전부 삭제라고 입력해 주세요. 삭제할 내역이 없다면 취소 또는 아니요 라고 입력해주세요."
            return {"ok": False, "message": message, "candidates": candidates}

        session.pop("pending_action", None)
        session.pop("pending_delete_candidates", None)
        auth_sessions[session_key] = session

        return {"ok": True, "message": "삭제 완료"}
    if tool_name == "delete_income_by_chat":
        result = backend_api.delete_income_by_chat(
            auth_header=auth_header,
            date=arguments["date"],
            amount=int(arguments.get("amount", 0)),
            memo=arguments.get("memo", "")
        )

        if result.get("status") == 409:
            candidates = result["candidates"]

            session["pending_action"] = "delete"
            session["pending_delete_candidates"] = candidates
            session["pending_tx_type"] = "INCOME"
            auth_sessions[session_key] = session

            message = "삭제 가능한 수입 후보가 여러 개 있습니다:\n"
            for c in candidates:
                message += f'{c["number"]}번. {c["date"]} {c["amount"]}원 "{c["memo"]}" [{c["category"]}]\n'
            message += "\n삭제 할 내역의 번호를 말해주세요. 모두 삭제를 원하시면 모두 삭제 또는 전부 삭제라고 입력해 주세요. 삭제할 내역이 없다면 취소 또는 아니요 라고 입력해주세요."
            return {"ok": False, "message": message, "candidates": candidates}

        session.pop("pending_action", None)
        session.pop("pending_delete_candidates", None)
        auth_sessions[session_key] = session

        return {"ok": True, "message": "수입 삭제 완료"}
    if tool_name == "update_expense_by_chat":
        session_key = auth_header or "anonymous"
        session = auth_sessions.get(session_key, {})
        result = backend_api.update_expense_by_chat(
            auth_header=auth_header,
            date=arguments.get("date", ""),
            amount=int(arguments.get("amount", 0)),
            memo=arguments.get("memo", "")
        )

        candidates = result.get("candidates", [])

        if not candidates:
            return {"ok": True, "message": "수정할 지출 내역이 없습니다."}

        # 후보군 저장
        session["pending_action"] = "update"
        session["pending_update_candidates"] = candidates
        session["pending_tx_type"] = "EXPENSE"
        auth_sessions[session_key] = session

        # 후보가 1개든 여러 개든 무조건 선택 유도
        message = "수정할 항목을 선택하고 수정 내용을 말씀해주세요. 수정할 내역이 없다면 취소 또는 아니요 라고 입력해주세요.:\n"
        for c in candidates:
            message += f'{c["number"]}번. {c["date"]} {c["amount"]}원 "{c["memo"]}"\n'
        message += "\n예: 1번 금액 xxxx원으로 수정. 날짜 어제로 수정. 메모 xx로 수정."

        return {"ok": False, "message": message, "candidates": candidates}
    if tool_name == "update_income_by_chat":
        session_key = auth_header or "anonymous"
        session = auth_sessions.get(session_key, {})

        result = backend_api.update_income_by_chat(
            auth_header=auth_header,
            date=arguments.get("date", ""),
            amount=int(arguments.get("amount", 0)),
            memo=arguments.get("memo", "")
        )

        candidates = result.get("candidates", [])

        if not candidates:
            return {"ok": True, "message": "수정할 수입 내역이 없습니다."}

        session["pending_action"] = "update"
        session["pending_update_candidates"] = candidates
        session["pending_tx_type"] = "INCOME"
        auth_sessions[session_key] = session

        message = "수정할 수입 항목을 선택하고 수정 내용을 말씀해주세요. 수정할 내역이 없다면 취소 또는 아니요 라고 입력해주세요.:\n"
        for c in candidates:
            message += f'{c["number"]}번. {c["date"]} {c["amount"]}원 "{c["memo"]}"\n'
        message += "\n예: 1번 금액 xxxx원으로 수정. 날짜 어제로 수정. 메모 xx로 수정."

        return {"ok": False, "message": message, "candidates": candidates}

    if tool_name == "get_expense_summary":
        result = backend_api.get_expense_summary(
            auth_header=auth_header,
            period=arguments["period"],
            date=arguments.get("date")
        )

        if not result.get("ok"):
            return result
        
        message = (
            f'{result["start"]} 지출액은 {result["totalAmount"]:,}원입니다.'
            if result["period"] == "day"
            else (
                f'({result["start"]} ~ {result["end"]})의 '
                f'총 지출액은 {result["totalAmount"]:,}원입니다.'
            )
        )
        return {
            "ok": True,
            "message": message,
            "type": result["type"],
            "period": result["period"],
            "baseDate": result["baseDate"],
            "start": result["start"],
            "end": result["end"],
            "totalAmount": result["totalAmount"],
        }


    if tool_name == "get_income_summary":
        result = backend_api.get_income_summary(
            auth_header=auth_header,
            period=arguments["period"],
            date=arguments.get("date")
        )

        if not result.get("ok"):
            return result

        message = (
            f'{result["start"]} 수입액은 {result["totalAmount"]:,}원입니다.'
            if result["period"] == "day"
            else (
                f'({result["start"]} ~ {result["end"]})의 '
                f'총 수입액은 {result["totalAmount"]:,}원입니다.'
            )
        )

        return {
            "ok": True,
            "message": message,
            "type": result["type"],
            "period": result["period"],
            "baseDate": result["baseDate"],
            "start": result["start"],
            "end": result["end"],
            "totalAmount": result["totalAmount"],
        }

    if tool_name == "get_top_expense_category":
        result = backend_api.get_top_expense_category(
            auth_header=auth_header,
            period=arguments["period"],
            date=arguments.get("date")
        )

        if not result.get("ok"):
            return result

        category = result.get("category")
        total = int(result.get("totalAmount", 0))
        start = result.get("start")
        end = result.get("end")

        period = result.get("period")

        # 기간 표시 문자열 만들기
        if period == "day":
            period_text = f"{start}"   # start == end == 해당 날짜
        else:
            period_text = f"{start} ~ {end}"

        # 지출 데이터가 없는 경우
        if not category or total == 0:
            message = f"({period_text}) 기간 동안 지출 내역이 없습니다."
        else:
            message = (
                f"({period_text}) 기간 동안 "
                f'가장 많이 지출한 카테고리는 '
                f'"{category}"이며 {total:,}원입니다.'
            )


        return {
            "ok": True,
            "message": message,
            "period": result.get("period"),
            "category": category,
            "totalAmount": total,
            "start": start,
            "end": end,
        }



    # reply-controller (CRUD)
    if tool_name == "create_reply":
        return backend_api.create_reply(
            auth_header=auth_header,
            bno=int(arguments["bno"]),
            content=arguments["content"]
        )
    if tool_name == "list_replies":
        return backend_api.list_replies(
            auth_header=auth_header,
            bno=int(arguments["bno"]),
            limit=int(arguments.get("limit", 10))
        )
    if tool_name == "delete_reply":
        return backend_api.delete_reply(
            auth_header=auth_header,
            reply_id=int(arguments["reply_id"])
        )
    if tool_name == "update_reply":
        return backend_api.update_reply(
            auth_header=auth_header,
            reply_id=int(arguments["reply_id"]),
            content=arguments["content"]
        )
    
    # notice-controller (CRUD)
    if tool_name == "create_notice":
        return backend_api.create_notice(
            auth_header=auth_header,
            title=arguments["title"],
            content=arguments["content"],
            imageUrl=arguments.get("imageUrl", "")
        )
    if tool_name == "list_notices":
        return backend_api.list_notices(
            auth_header=auth_header,
            limit=int(arguments.get("limit", 10))
        )
    if tool_name == "delete_notice":
        return backend_api.delete_notice(
            auth_header=auth_header,
            notice_id=int(arguments["notice_id"])
        )
    if tool_name == "update_notice":
        return backend_api.update_notice(
            auth_header=auth_header,
            notice_id=int(arguments["notice_id"]),
            title=arguments["title"],
            content=arguments["content"],
            imageUrl=arguments.get("imageUrl", "")
        )

    # member-controller (CRUD)
    if tool_name == "list_members":
        return backend_api.list_members(
            auth_header=auth_header,
            limit=int(arguments.get("limit", 10))
        )
    if tool_name == "verify_password":
        return backend_api.verify_password(
            auth_header=auth_header,
            password=arguments["password"]
        )
    if tool_name == "delete_member":
        return backend_api.delete_member(
            auth_header=auth_header,
            member_id=int(arguments["member_id"])
        )
    if tool_name == "update_member_info":
        return backend_api.update_member_info(
            auth_header=auth_header,
            nickname=arguments.get("nickname"),
            password=arguments.get("password")
        )

    # budget-controller (CRUD)
    if tool_name == "create_budget":
        return backend_api.create_budget(
            auth_header=auth_header,
            year=int(arguments["year"]),
            month=int(arguments["month"]),
            limitAmount=int(arguments["limitAmount"]),
            usedAmount=int(arguments.get("usedAmount", 0))
        )
    if tool_name == "list_budgets":
        return backend_api.list_budgets(
            auth_header=auth_header,
            mid=int(arguments["mid"]),
            limit=int(arguments.get("limit", 10))
        )
    if tool_name == "adjust_budget_limit":
        return backend_api.adjust_budget_limit(
            auth_header=auth_header,
            mid=int(arguments["mid"]),
            delta=int(arguments["delta"])
        )

    # board-controller (CRUD)
    if tool_name == "create_board":
        return backend_api.create_board(
            auth_header=auth_header,
            title=arguments["title"],
            content=arguments["content"],
            imageUrl=arguments.get("imageUrl", "")
        )
    if tool_name == "get_board":
        return backend_api.get_board(
            auth_header=auth_header,
            board_id=int(arguments["board_id"])
        )
    if tool_name == "delete_board":
        return backend_api.delete_board(
            auth_header=auth_header,
            board_id=int(arguments["board_id"])
        )
    if tool_name == "list_boards":
        return backend_api.list_boards(
            auth_header=auth_header,
            page=int(arguments.get("page", 1)),
            limit=int(arguments.get("limit", 10)),
            keyword=arguments.get("keyword", ""),
            types=arguments.get("types", "")
        )
    if tool_name == "update_board":
        return backend_api.update_board(
            auth_header=auth_header,
            board_id=int(arguments["board_id"]),
            title=arguments["title"],
            content=arguments["content"],
            imageUrl=arguments.get("imageUrl", "")
        )

    # authentication-controller (only sign-in)
    if tool_name == "sign_in":
        return backend_api.sign_in(
            auth_header=auth_header,
            username=arguments["username"],
            password=arguments["password"]
        )


    return {"ok": False, "error": f"Unknown tool: {tool_name}"}

def parse_user_selection(message: str) -> list[int]:
    """
    "4번 삭제" → [4], "1,3,5" → [1,3,5]
    """
    import re
    numbers = re.findall(r"\d+", message)
    return [int(n) for n in numbers] if numbers else []

def format_transaction_reply(t: dict) -> str:
    return (
        f'{t["date"]} {t["amount"]}원 '
        f'"{t.get("memo","")}" '
        f'[{t.get("category","")}] 등록 완료'
    )

def build_summary_message(result, is_expense=True):
    amount = f'{result["totalAmount"]:,}원'
    label = "지출액" if is_expense else "수입액"
    period = result["period"]

    if period == "day":
        return f'{result["start"]} {label}은 {amount}입니다.'
    else:
        return (
            f'({result["start"]} ~ {result["end"]})의 '
            f'총 {label}은 {amount}입니다.'
        )

def require_login(auth_header: Optional[str]) -> Optional[Dict[str, Any]]:
    if not auth_header:
        return {
            "ok": False,
            "message": "서비스 이용을 위해 로그인 또는 회원가입이 필요합니다."
        }
    return None
