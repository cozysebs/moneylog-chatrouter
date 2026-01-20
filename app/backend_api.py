# app/backend_api.py
from __future__ import annotations
import os
import requests
from typing import Any, Dict, List, Optional

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8080")
TIMEOUT_SEC = float(os.getenv("BACKEND_TIMEOUT_SEC", "5"))

def _headers(auth_header: Optional[str]) -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if auth_header:
        h["Authorization"] = auth_header  # "Bearer eyJ..."
    return h

def create_expense(auth_header: Optional[str], date: str, amount: int, category: str, memo: str = "") -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/transactions"
    payload = {
        "type": "EXPENSE",
        "amount": int(amount),
        "category": category,
        "memo": memo or "",
        "date": date,  # "YYYY-MM-DD"
    }
    r = requests.post(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT_SEC)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "Backend 인증 실패(Authorization 전달 필요)"}

    r.raise_for_status()
    # 백엔드 컨트롤러는 Long(id)만 반환
    expense_id = r.json()
    return {"ok": True, "expense_id": expense_id}

def list_expenses(auth_header: Optional[str], limit: int = 10) -> Dict[str, Any]:
    safe_limit = max(1, min(int(limit), 50))
    url = f"{BACKEND_BASE_URL}/api/transactions/recent"
    r = requests.get(url, params={"limit": safe_limit}, headers=_headers(auth_header), timeout=TIMEOUT_SEC)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "Backend 인증 실패(Authorization 전달 필요)"}

    r.raise_for_status()
    items: List[Dict[str, Any]] = r.json()
    # Router tool 결과로 쓰기 좋게 축약
    simplified = [
        {
            "id": it.get("id"),
            "date": it.get("date"),
            "amount": it.get("amount"),
            "category": it.get("category"),
            "memo": it.get("memo"),
            "type": it.get("type"),
        }
        for it in items
    ]
    return {"ok": True, "items": simplified}

def delete_expense(auth_header: Optional[str], expense_id: int) -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/transactions/{int(expense_id)}"
    r = requests.delete(url, headers=_headers(auth_header), timeout=TIMEOUT_SEC)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "Backend 인증 실패(Authorization 전달 필요)"}

    r.raise_for_status()
    return {"ok": True, "deleted_id": int(expense_id)}