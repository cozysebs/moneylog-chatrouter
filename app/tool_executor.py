# app/tool_executor.py
from __future__ import annotations
from typing import Any, Dict, Optional

from app import backend_api

def execute_tool_call(tool_name: str, arguments: Dict[str, Any], auth_header: Optional[str]) -> Dict[str, Any]:
    """
    모델이 요청한 tool call을 실제 '백엔드 REST API'로 실행하고 결과를 dict로 반환한다.
    auth_header: Backend가 Router로 전달한 "Authorization: Bearer <JWT>" 값
    """
    # transaction-controller (CRUD)
    if tool_name == "create_expense":
        return backend_api.create_expense(
            auth_header=auth_header,
            date=arguments["date"],
            amount=int(arguments["amount"]),
            category=arguments["category"],
            memo=arguments.get("memo", "")
        )
    if tool_name == "list_expenses":
        return backend_api.list_expenses(
            auth_header=auth_header,
            limit=int(arguments.get("limit", 10))
        )
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