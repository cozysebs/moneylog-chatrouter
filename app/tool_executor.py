# app/tool_executor.py
from __future__ import annotations
from typing import Any, Dict, Optional

from app import backend_api

def execute_tool_call(tool_name: str, arguments: Dict[str, Any], auth_header: Optional[str]) -> Dict[str, Any]:
    """
    모델이 요청한 tool call을 실제 '백엔드 REST API'로 실행하고 결과를 dict로 반환한다.
    auth_header: Backend가 Router로 전달한 "Authorization: Bearer <JWT>" 값
    """
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

    return {"ok": False, "error": f"Unknown tool: {tool_name}"}