# app/backend_api.py
from __future__ import annotations
import os
import requests
from typing import Any, Dict, List, Optional, Tuple

BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://localhost:8080")

# timeout을 '짧고 명확하게' (connect, read)
CONNECT_TIMEOUT = float(os.getenv("BACKEND_CONNECT_TIMEOUT_SEC", "2"))
READ_TIMEOUT = float(os.getenv("BACKEND_READ_TIMEOUT_SEC", "10"))
TIMEOUT: Tuple[float, float] = (CONNECT_TIMEOUT, READ_TIMEOUT)

# 연결 재사용(Session)
_SESSION = requests.Session()

def _headers(auth_header: Optional[str]) -> Dict[str, str]:
    h = {"Content-Type": "application/json"}
    if auth_header:
        h["Authorization"] = auth_header
    return h



# transaction-controller (CRUD)
def create_expense(auth_header: Optional[str], date: str, amount: int, category: str, memo: str = "") -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/transactions"
    payload = {
        "type": "EXPENSE",
        "amount": int(amount),
        "category": category,
        "memo": memo or "",
        "date": date,
    }
    r = _SESSION.post(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "Backend 인증 실패(Authorization 전달 필요)"}

    r.raise_for_status()
    expense_id = r.json()
    return {
        "ok": True,
        "message": f"{date} {amount}원 \"{memo}\" [{category}] 등록 완료",
        "item": {
            "id": expense_id,
            "date": date,
            "amount": amount,
            "category": category,
            "memo": memo,
            "type": "EXPENSE"
        }
    }

def list_expenses(auth_header: Optional[str], limit: int = 10) -> Dict[str, Any]:
    safe_limit = max(1, min(int(limit), 50))
    url = f"{BACKEND_BASE_URL}/api/transactions/recent"
    r = _SESSION.get(url, params={"limit": safe_limit, "type":"EXPENSE"}, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "Backend 인증 실패(Authorization 전달 필요)"}

    r.raise_for_status()
    items: List[Dict[str, Any]] = r.json()
    simplified = [
        {
            # "id": it.get("id"),
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
    r = _SESSION.delete(url, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "Backend 인증 실패(Authorization 전달 필요)"}

    if r.status_code == 403:
        return {"ok": False, "error": "FORBIDDEN", "detail": "본인 거래 내역만 삭제할 수 있음"}

    r.raise_for_status()
    return {"ok": True, "deleted_id": int(expense_id)}

def update_expense(
        auth_header: Optional[str],
        expense_id: int,
        date: str,
        amount: int,
        category: str,
        memo: str = "",
) -> Dict[str, Any]:
    """지출 수정(PUT /api/transactions)."""
    url = f"{BACKEND_BASE_URL}/api/transactions"
    payload = {
        "id": int(expense_id),
        "type": "EXPENSE",
        "amount": int(amount),
        "category": category,
        "memo": memo or "",
        "date": date,
    }
    r = _SESSION.put(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "Backend 인증 실패(Authorization 전달 필요)"}
    if r.status_code == 403:
        return {"ok": False, "error": "FORBIDDEN", "detail": "본인 거래 내역만 수정할 수 있음"}
    if r.status_code == 404:
        return {"ok": False, "error": "NOT_FOUND", "detail": "해당 지출 ID를 찾을 수 없음"}

    r.raise_for_status()
    return {"ok": True, "updated_id": int(expense_id)}

def delete_expense_by_chat(auth_header, date, amount=0, memo=""):
    url = f"{BACKEND_BASE_URL}/api/transactions/chat/delete"
    payload = {"date": date, "amount": amount, "memo": memo or "", "type":"EXPENSE"}

    r = _SESSION.post(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 409:
        return {
            "ok": True,
            "status": 409,
            "candidates": r.json()
        }

    r.raise_for_status()
    return {"ok": True, "status": 200}

def confirm_delete_by_chat(auth_header, selected_indexes):
    url = f"{BACKEND_BASE_URL}/api/transactions/chat/delete/confirm"
    payload = {"selectedIndexes": selected_indexes, "type":"EXPENSE"}

    r = _SESSION.post(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)
    r.raise_for_status()
    
    return {
        "ok": True,
        "status": r.status_code,
        "message": r.json().get("message", "선택된 항목 삭제 완료")
    }

def update_expense_by_chat(auth_header: Optional[str], date: Optional[str] = None, amount: Optional[int] = None, memo: Optional[str] = None) -> Dict[str, Any]:
    """
    날짜/금액/메모 기준으로 후보 지출 내역 조회
    - 후보가 1개 이상일 때 status=409 + 후보 목록 반환
    """
    url = f"{BACKEND_BASE_URL}/api/transactions/chat/update"
    payload: Dict[str, Any] = {
        "type":"EXPENSE"
    }

    if date:
        payload["date"] = date
    if amount is not None:
        payload["amount"] = int(amount)
    if memo:
        payload["memo"] = memo

    r = _SESSION.post(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 409:
        candidates = r.json().get("candidates", [])
        # 후보를 번호/날짜/금액/메모 형태로 간단히 구조화
        structured = [
            {
                "number": c.get("number"),
                "date": c.get("date"),
                "amount": c.get("amount"),
                "memo": c.get("memo", "")
            }
            for c in candidates
        ]
        return {"ok": True, "status": 409, "candidates": structured}

    r.raise_for_status()
    return {"ok": True, "status": 200}


def confirm_update_by_chat(
    auth_header: Optional[str],
    selected_index: int,
    new_date: Optional[str] = None,
    new_amount: Optional[int] = None,
    new_memo: Optional[str] = None
) -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/transactions/chat/update/confirm"

    # ✅ DTO 구조에 맞게 newData 안에 넣기
    payload: Dict[str, Any] = {
        "candidateIndex": int(selected_index),
        "newData": {} , # 반드시 dict로 초기화
        "type" : "EXPENSE"
    }

    if new_date is not None:
        payload["newData"]["date"] = new_date
    if new_amount is not None:
        payload["newData"]["amount"] = int(new_amount)
    if new_memo is not None:
        payload["newData"]["memo"] = new_memo

    # 최소 1개 수정값 필요
    if not payload["newData"]:
        return {
            "ok": False,
            "error": "BAD_REQUEST",
            "detail": "수정할 값(date/amount/memo) 중 최소 1개 필요"
        }

    print("[DEBUG] Sending to Backend (corrected):", payload)
    print("[DEBUG] Authorization Header:", auth_header)

    r = _SESSION.post(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    print(f"[DEBUG] Backend Response ({r.status_code}): {r.text}")

    r.raise_for_status()

    return {
        "ok": True,
        "status": r.status_code,
        "message": r.json().get("message", "선택한 항목 수정 완료")
    }

def create_income(auth_header: Optional[str], date: str, amount: int, category: str, memo: str = "") -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/transactions"
    payload = {
        "type": "INCOME",
        "amount": int(amount),
        "category": category,
        "memo": memo or "",
        "date": date,
    }
    r = _SESSION.post(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "Backend 인증 실패(Authorization 전달 필요)"}

    r.raise_for_status()
    income_id = r.json()
    return {
        "ok": True,
        "message": f"{date} {amount}원 \"{memo}\" [{category}] 수입 등록 완료",
        "item": {
            "id": income_id,
            "date": date,
            "amount": amount,
            "category": category,
            "memo": memo,
            "type": "INCOME"
        }
    }

def list_incomes(auth_header: Optional[str], limit: int = 10) -> Dict[str, Any]:
    safe_limit = max(1, min(int(limit), 50))
    url = f"{BACKEND_BASE_URL}/api/transactions/recent"
    r = _SESSION.get(
        url,
        params={"limit": safe_limit, "type": "INCOME"},
        headers=_headers(auth_header),
        timeout=TIMEOUT
    )

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "Backend 인증 실패(Authorization 전달 필요)"}

    r.raise_for_status()
    items: List[Dict[str, Any]] = r.json()
    simplified = [
        {
            "date": it.get("date"),
            "amount": it.get("amount"),
            "category": it.get("category"),
            "memo": it.get("memo"),
            "type": it.get("type"),
        }
        for it in items
    ]
    return {"ok": True, "items": simplified}

def delete_income_by_chat(auth_header, date, amount=0, memo=""):
    url = f"{BACKEND_BASE_URL}/api/transactions/chat/delete"
    payload = {
        "date": date,
        "amount": amount,
        "memo": memo or "",
        "type": "INCOME"
    }

    r = _SESSION.post(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 409:
        return {
            "ok": True,
            "status": 409,
            "candidates": r.json()
        }

    r.raise_for_status()
    return {"ok": True, "status": 200}

def confirm_delete_income_by_chat(auth_header, selected_indexes):
    url = f"{BACKEND_BASE_URL}/api/transactions/chat/delete/confirm"
    payload = {
        "selectedIndexes": selected_indexes,
        "type": "INCOME"
    }

    r = _SESSION.post(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)
    r.raise_for_status()
    
    return {
        "ok": True,
        "status": r.status_code,
        "message": r.json().get("message", "선택된 항목 삭제 완료")
    }

def update_income_by_chat(
    auth_header: Optional[str],
    date: Optional[str] = None,
    amount: Optional[int] = None,
    memo: Optional[str] = None
) -> Dict[str, Any]:
    """
    날짜/금액/메모 기준으로 후보 수입 내역 조회
    - 후보가 1개 이상일 때 status=409 + 후보 목록 반환
    """
    url = f"{BACKEND_BASE_URL}/api/transactions/chat/update"
    payload: Dict[str, Any] = {
        "type": "INCOME"
    }

    if date:
        payload["date"] = date
    if amount is not None:
        payload["amount"] = int(amount)
    if memo:
        payload["memo"] = memo

    r = _SESSION.post(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 409:
        candidates = r.json().get("candidates", [])
        structured = [
            {
                "number": c.get("number"),
                "date": c.get("date"),
                "amount": c.get("amount"),
                "memo": c.get("memo", "")
            }
            for c in candidates
        ]
        return {"ok": True, "status": 409, "candidates": structured}

    r.raise_for_status()
    return {"ok": True, "status": 200}

def update_income_by_chat(
    auth_header: Optional[str],
    date: Optional[str] = None,
    amount: Optional[int] = None,
    memo: Optional[str] = None
) -> Dict[str, Any]:
    """
    날짜/금액/메모 기준으로 후보 수입 내역 조회
    - 후보가 1개 이상일 때 status=409 + 후보 목록 반환
    """
    url = f"{BACKEND_BASE_URL}/api/transactions/chat/update"
    payload: Dict[str, Any] = {
        "type": "INCOME"
    }

    if date:
        payload["date"] = date
    if amount is not None:
        payload["amount"] = int(amount)
    if memo:
        payload["memo"] = memo

    r = _SESSION.post(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 409:
        candidates = r.json().get("candidates", [])
        structured = [
            {
                "number": c.get("number"),
                "date": c.get("date"),
                "amount": c.get("amount"),
                "memo": c.get("memo", "")
            }
            for c in candidates
        ]
        return {"ok": True, "status": 409, "candidates": structured}

    r.raise_for_status()
    return {"ok": True, "status": 200}

def confirm_update_income_by_chat(
    auth_header: Optional[str],
    selected_index: int,
    new_date: Optional[str] = None,
    new_amount: Optional[int] = None,
    new_memo: Optional[str] = None
) -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/transactions/chat/update/confirm"

    payload: Dict[str, Any] = {
        "candidateIndex": int(selected_index),
        "newData": {},
        "type": "INCOME"
    }

    if new_date is not None:
        payload["newData"]["date"] = new_date
    if new_amount is not None:
        payload["newData"]["amount"] = int(new_amount)
    if new_memo is not None:
        payload["newData"]["memo"] = new_memo

    if not payload["newData"]:
        return {
            "ok": False,
            "error": "BAD_REQUEST",
            "detail": "수정할 값(date/amount/memo) 중 최소 1개 필요"
        }

    print("[DEBUG] Sending to Backend:", payload)

    r = _SESSION.post(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    print(f"[DEBUG] Backend Response ({r.status_code}): {r.text}")

    r.raise_for_status()

    return {
        "ok": True,
        "status": r.status_code,
        "message": r.json().get("message", "선택한 항목 수정 완료")
    }


# reply-controller (CRUD)
def create_reply(auth_header: Optional[str], bno: int, content: str) -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/replies"
    payload = {"bno": int(bno), "content": content}
    r = _SESSION.post(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "Backend 인증 실패(Authorization 전달 필요)"}

    r.raise_for_status()
    reply_id = r.json()  # ReplyController는 Long id 반환
    return {"ok": True, "reply_id": reply_id}

def list_replies(auth_header: Optional[str], bno: int, limit: int = 10) -> Dict[str, Any]:
    # PageRequestDTO.size 최소 10이라 limit은 10~20으로 clamp
    size = max(10, min(int(limit), 20))
    url = f"{BACKEND_BASE_URL}/api/replies/board/{int(bno)}"
    r = _SESSION.get(url, params={"page": 1, "size": size}, headers=_headers(auth_header), timeout=TIMEOUT)

    r.raise_for_status()
    data = r.json()

    # 페이로드 축소(Phase2-lite: 결과 크기/필드 제한)
    dto_list: List[Dict[str, Any]] = data.get("dtoList", []) or []
    simplified = [
        {
            "id": it.get("id"),
            "content": it.get("content"),
            "deleted": it.get("deleted"),
            "mid": it.get("mid"),
            "nickname": it.get("nickname"),
        }
        for it in dto_list
    ]
    return {"ok": True, "items": simplified, "total": data.get("total")}

def delete_reply(auth_header: Optional[str], reply_id: int) -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/replies/{int(reply_id)}"
    r = _SESSION.delete(url, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "Backend 인증 실패(Authorization 전달 필요)"}
    if r.status_code == 403:
        return {"ok": False, "error": "FORBIDDEN", "detail": "본인 댓글만 삭제할 수 있음"}
    if r.status_code == 404:
        return {"ok": False, "error": "NOT_FOUND", "detail": "해당 댓글 ID를 찾을 수 없음"}

    r.raise_for_status()
    return {"ok": True, "deleted_id": int(reply_id)}

def update_reply(auth_header: Optional[str], reply_id: int, content: str) -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/replies/{int(reply_id)}"
    payload = {"content": content}
    r = _SESSION.put(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "Backend 인증 실패(Authorization 필요)"}
    if r.status_code == 403:
        return {"ok": False, "error": "FORBIDDEN", "detail": "본인 댓글만 수정할 수 있음"}
    if r.status_code == 404:
        return {"ok": False, "error": "NOT_FOUND", "detail": "해당 댓글 ID를 찾을 수 없음"}

    r.raise_for_status()
    return {"ok": True, "updated_id": int(reply_id)}

# notice-controller (CRUD)
def create_notice(auth_header: Optional[str], title: str, content: str, imageUrl: str = "") -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/notices"
    payload = {"title": title, "content": content, "imageUrl": imageUrl or ""}
    r = _SESSION.post(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "Backend 인증 실패(Authorization 필요)"}

    r.raise_for_status()
    notice_id = r.json()
    return {"ok": True, "notice_id": notice_id}

def list_notices(auth_header: Optional[str], limit: int = 10) -> Dict[str, Any]:
    size = max(10, min(int(limit), 20))
    url = f"{BACKEND_BASE_URL}/api/notices/list"
    r = _SESSION.get(url, params={"page": 1, "size": size}, headers=_headers(auth_header), timeout=TIMEOUT)

    r.raise_for_status()
    data = r.json()

    dto_list = data.get("dtoList", []) or []
    simplified = [
        {
            "id": it.get("id"),
            "title": it.get("title"),
            "createTime": it.get("createTime"),
            "mid": it.get("mid"),
            "nickname": it.get("nickname"),
        }
        for it in dto_list
    ]
    return {"ok": True, "items": simplified, "total": data.get("total")}

def delete_notice(auth_header: Optional[str], notice_id: int) -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/notices/{int(notice_id)}"
    r = _SESSION.delete(url, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "Backend 인증 실패(Authorization 필요)"}
    if r.status_code == 403:
        return {"ok": False, "error": "FORBIDDEN", "detail": "본인 공지사항만 삭제할 수 있음"}
    if r.status_code == 404:
        return {"ok": False, "error": "NOT_FOUND", "detail": "해당 공지 ID를 찾을 수 없음"}

    r.raise_for_status()
    return {"ok": True, "deleted_id": int(notice_id)}

def update_notice(
    auth_header: Optional[str],
    notice_id: int,
    title: str,
    content: str,
    imageUrl: str = ""
) -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/notices/{int(notice_id)}"
    payload = {"title": title, "content": content, "imageUrl": imageUrl or ""}

    r = _SESSION.put(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "Backend 인증 실패(Authorization 필요)"}
    if r.status_code == 403:
        return {"ok": False, "error": "FORBIDDEN", "detail": "본인 공지사항만 수정할 수 있음"}
    if r.status_code == 404:
        return {"ok": False, "error": "NOT_FOUND", "detail": "해당 공지 ID를 찾을 수 없음"}

    r.raise_for_status()
    return {"ok": True, "updated_id": int(notice_id)}

# member-controller (CRUD)
def list_members(auth_header: Optional[str], limit: int = 10) -> Dict[str, Any]:
    size = max(10, min(int(limit), 20))
    url = f"{BACKEND_BASE_URL}/api/members/list"
    r = _SESSION.get(url, params={"page": 1, "size": size}, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "로그인이 필요함"}
    if r.status_code == 403:
        return {"ok": False, "error": "FORBIDDEN", "detail": "관리자만 조회 가능"}

    r.raise_for_status()
    data = r.json()

    # 결과 크기 제한(Phase2-lite): 핵심 필드만
    dto_list: List[Dict[str, Any]] = data.get("dtoList", []) or []
    simplified = [
        {
            "id": it.get("id"),
            "username": it.get("username"),
            "nickname": it.get("nickname"),
            "role": it.get("role"),
        }
        for it in dto_list
    ]
    return {"ok": True, "items": simplified, "total": data.get("total")}

def verify_password(auth_header: Optional[str], password: str) -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/members/verify-password"
    payload = {"password": password}
    r = _SESSION.post(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "로그인이 필요함"}
    if r.status_code == 400:
        return {"ok": False, "error": "BAD_REQUEST", "detail": "password가 필요함"}

    r.raise_for_status()
    return {"ok": True, "matches": bool(r.json())}

def delete_member(auth_header: Optional[str], member_id: int) -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/members/{int(member_id)}"
    r = _SESSION.delete(url, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "로그인이 필요함"}
    if r.status_code == 403:
        return {"ok": False, "error": "FORBIDDEN", "detail": "본인 또는 관리자만 삭제 가능"}

    r.raise_for_status()
    return {"ok": True, "deleted_id": int(member_id)}

def update_member_info(
    auth_header: Optional[str],
    nickname: Optional[str] = None,
    password: Optional[str] = None
) -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/members/change-info"

    payload: Dict[str, Any] = {}
    if nickname is not None:
        payload["nickname"] = nickname
    if password is not None:
        payload["password"] = password

    # 최소 1개는 있어야 함(백엔드도 400 처리하지만, Router에서도 즉시 방어)
    if not payload:
        return {"ok": False, "error": "BAD_REQUEST", "detail": "nickname 또는 password 중 최소 1개가 필요함"}

    r = _SESSION.put(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "로그인이 필요함"}
    if r.status_code == 400:
        return {"ok": False, "error": "BAD_REQUEST", "detail": "입력값이 유효하지 않음"}

    r.raise_for_status()
    return {"ok": True}

# budget-controller (CRUD)
def create_budget(
    auth_header: Optional[str],
    year: int,
    month: int,
    limitAmount: int,
    usedAmount: int = 0
) -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/budget"
    payload = {
        "year": int(year),
        "month": int(month),
        "limitAmount": int(limitAmount),
        "usedAmount": int(usedAmount),
    }
    r = _SESSION.post(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "로그인이 필요함"}

    r.raise_for_status()
    return {"ok": True}

def list_budgets(auth_header: Optional[str], mid: int, limit: int = 10) -> Dict[str, Any]:
    size = max(10, min(int(limit), 20))
    url = f"{BACKEND_BASE_URL}/api/budget/list/{int(mid)}"
    r = _SESSION.get(url, params={"page": 1, "size": size}, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "로그인이 필요함"}

    r.raise_for_status()
    data = r.json()

    # Phase2-lite: 결과 필드 축소
    dto_list: List[Dict[str, Any]] = data.get("dtoList", []) or []
    simplified = [
        {
            "id": it.get("id"),
            "year": it.get("year"),
            "month": it.get("month"),
            "limitAmount": it.get("limitAmount"),
            "usedAmount": it.get("usedAmount"),
        }
        for it in dto_list
    ]
    return {"ok": True, "items": simplified, "total": data.get("total")}

def adjust_budget_limit(auth_header: Optional[str], mid: int, delta: int) -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/budget/limit/{int(mid)}"

    # PATCH + query param(delta)
    r = _SESSION.patch(
        url,
        params={"delta": int(delta)},
        headers=_headers(auth_header),
        timeout=TIMEOUT
    )

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "로그인이 필요함"}
    if r.status_code == 403:
        return {"ok": False, "error": "FORBIDDEN", "detail": "본인(mid)만 예산을 조정할 수 있음"}
    if r.status_code == 400:
        return {"ok": False, "error": "BAD_REQUEST", "detail": "delta 값이 유효하지 않음"}

    r.raise_for_status()
    return {"ok": True, "mid": int(mid), "delta": int(delta)}

# board-controller (CRUD)
def create_board(auth_header: Optional[str], title: str, content: str, imageUrl: str = "") -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/boards"
    payload = {"title": title, "content": content, "imageUrl": imageUrl or ""}
    r = _SESSION.post(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "로그인이 필요함"}

    r.raise_for_status()
    board_id = r.json()
    return {"ok": True, "board_id": int(board_id)}

def get_board(auth_header: Optional[str], board_id: int) -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/boards/{int(board_id)}"
    r = _SESSION.get(url, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 404:
        return {"ok": False, "error": "NOT_FOUND", "detail": "해당 게시글을 찾을 수 없음"}

    r.raise_for_status()
    data = r.json()

    # Phase2-lite: 결과 크기 제한(필드 축소)
    return {"ok": True, "board": {
        "id": data.get("id"),
        "title": data.get("title"),
        "content": data.get("content"),
        "mid": data.get("mid"),
        "nickname": data.get("nickname"),
        "readcount": data.get("readcount"),
        "createTime": data.get("createTime"),
        "updateTime": data.get("updateTime"),
        "imageUrl": data.get("imageUrl"),
    }}

def delete_board(auth_header: Optional[str], board_id: int) -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/boards/{int(board_id)}"
    r = _SESSION.delete(url, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "로그인이 필요함"}
    if r.status_code == 403:
        return {"ok": False, "error": "FORBIDDEN", "detail": "본인 게시글만 삭제 가능"}
    if r.status_code == 404:
        return {"ok": False, "error": "NOT_FOUND", "detail": "해당 게시글을 찾을 수 없음"}

    r.raise_for_status()
    return {"ok": True, "deleted_id": int(board_id)}

def list_boards(
    auth_header: Optional[str],
    page: int = 1,
    limit: int = 10,
    keyword: str = "",
    types: str = ""
) -> Dict[str, Any]:
    size = max(10, min(int(limit), 20))
    page = max(1, int(page))

    url = f"{BACKEND_BASE_URL}/api/boards/list"

    params: Dict[str, Any] = {"page": page, "size": size}
    if keyword:
        params["keyword"] = keyword
    if types:
        # PageRequestDTO에서 types를 어떤 형태로 받는지에 맞춰 전달해야 함.
        # 일반적으로 types=t&types=c 형태를 기대하면 리스트로 보내야 하나,
        # 현재는 최소 구현으로 문자열 그대로 전달(백엔드가 문자열 파싱이면 그대로 동작).
        params["types"] = types

    r = _SESSION.get(url, params=params, headers=_headers(auth_header), timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()

    # Phase2-lite: 결과 크기 제한(목록은 핵심 필드만)
    dto_list: List[Dict[str, Any]] = data.get("dtoList", []) or []
    simplified = [
        {
            "id": it.get("id"),
            "title": it.get("title"),
            "nickname": it.get("nickname"),
            "readcount": it.get("readcount"),
            "createTime": it.get("createTime"),
        }
        for it in dto_list
    ]
    return {"ok": True, "items": simplified, "total": data.get("total"), "page": page, "size": size}

def update_board(
    auth_header: Optional[str],
    board_id: int,
    title: str,
    content: str,
    imageUrl: str = ""
) -> Dict[str, Any]:
    url = f"{BACKEND_BASE_URL}/api/boards/{int(board_id)}"
    payload = {"title": title, "content": content, "imageUrl": imageUrl or ""}

    r = _SESSION.put(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    if r.status_code == 401:
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "로그인이 필요함"}
    if r.status_code == 403:
        return {"ok": False, "error": "FORBIDDEN", "detail": "본인 게시글만 수정 가능"}
    if r.status_code == 404:
        return {"ok": False, "error": "NOT_FOUND", "detail": "해당 게시글을 찾을 수 없음"}

    r.raise_for_status()
    return {"ok": True, "updated_id": int(board_id)}

# authentication-controller (only sign-in)
def sign_in(auth_header: Optional[str], username: str, password: str) -> Dict[str, Any]:
    # auth_header는 sign-in에서는 보통 None (인증 전)
    url = f"{BACKEND_BASE_URL}/api/authentication/sign-in"
    payload = {"username": username, "password": password}

    r = _SESSION.post(url, json=payload, headers=_headers(auth_header), timeout=TIMEOUT)

    # 보통 인증 실패는 401/403 중 하나로 오므로 둘 다 처리(백엔드 구현에 따라 다름)
    if r.status_code in (401, 403):
        return {"ok": False, "error": "UNAUTHORIZED", "detail": "아이디 또는 비밀번호가 올바르지 않음"}

    r.raise_for_status()
    data = r.json()

    # Phase2-lite: 결과 크기 제한(불필요 필드 제거)
    return {
        "ok": True,
        "token": data.get("token"),
        "member": {
            "id": data.get("id"),
            "username": data.get("username"),
            "name": data.get("name"),
            "role": data.get("role"),
        }
    }
