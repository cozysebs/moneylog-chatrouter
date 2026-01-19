# app/memory_store.py
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import List, Dict, Any

@dataclass
class Expense:
    expense_id: int
    date: str
    amount: int
    category: str
    memo: str = ""

# 메모리 DB
_EXPENSES: List[Expense] = []
_NEXT_ID: int = 1

def create_expense(date: str, amount: int, category: str, memo: str = "") -> Dict[str, Any]:
    global _NEXT_ID
    e = Expense(expense_id=_NEXT_ID, date=date, amount=amount, category=category, memo=memo or "")
    _NEXT_ID += 1
    _EXPENSES.append(e)
    return {"ok": True, "expense": asdict(e)}

def list_expenses(limit: int = 10) -> Dict[str, Any]:
    items = list(reversed(_EXPENSES))[: max(1, limit)]
    return {"ok": True, "items": [asdict(x) for x in items], "total": len(_EXPENSES)}

def delete_expense(expense_id: int) -> Dict[str, Any]:
    global _EXPENSES
    before = len(_EXPENSES)
    _EXPENSES = [x for x in _EXPENSES if x.expense_id != expense_id]
    after = len(_EXPENSES)
    return {"ok": (after < before), "deleted": (before - after), "expense_id": expense_id}