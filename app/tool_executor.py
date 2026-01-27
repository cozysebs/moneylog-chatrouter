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
            return {
                "ok": False,
                "message": "삭제할 항목을 선택하지 않았습니다. '취소'라고 입력하면 삭제를 취소할 수 있습니다."
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
            return {
                "ok": False,
                "message": "삭제할 수입 항목을 선택하지 않았습니다. '취소'라고 입력하면 삭제를 취소할 수 있습니다."
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
    if tool_name == "create_expense":
        return backend_api.create_expense(
            auth_header=auth_header,
            date=arguments["date"],
            amount=int(arguments["amount"]),
            category=arguments["category"],
            memo=arguments.get("memo", "")
        )
    if tool_name == "create_income":
        return backend_api.create_income(
            auth_header=auth_header,
            date=arguments["date"],
            amount=int(arguments["amount"]),
            category=arguments["category"],
            memo=arguments.get("memo", "")
        )
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
        message = "수정할 항목을 선택하고 수정 내용을 말씀해주세요:\n"
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

        message = "수정할 수입 항목을 선택하고 수정 내용을 말씀해주세요:\n"
        for c in candidates:
            message += f'{c["number"]}번. {c["date"]} {c["amount"]}원 "{c["memo"]}"\n'
        message += "\n예: 1번 금액 xxxx원으로 수정. 날짜 어제로 수정. 메모 xx로 수정."

        return {"ok": False, "message": message, "candidates": candidates}



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
