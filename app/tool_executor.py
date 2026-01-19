# app/tool_executor.py
from __future__ import annotations
from typing import Any, Dict

from app import memory_store

def execute_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    모델이 요청한 tool call을 실제 함수로 실행하고,
    결과를 dict로 반환한다(이 dict를 tool_result의 output으로 넣는다).
    """
    if tool_name == "create_expense":
        return memory_store.create_expense(
            date=arguments["date"],
            amount=int(arguments["amount"]),
            category=arguments["category"],
            memo=arguments.get("memo", "")
        )

    if tool_name == "list_expenses":
        return memory_store.list_expenses(limit=int(arguments.get("limit", 10)))

    if tool_name == "delete_expense":
        return memory_store.delete_expense(expense_id=int(arguments["expense_id"]))

    # 알 수 없는 tool
    return {"ok": False, "error": f"Unknown tool: {tool_name}"}