TOOLS = [
    {
        "type": "function",
        "name": "create_expense",
        "description": (
            "사용자가 지출을 '추가/기록/등록'하길 원할 때 호출한다. "
            "예: '어제 식비 12000원 썼어', '교통비 1500원 추가해줘'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "날짜(YYYY-MM-DD)",
                    "pattern": r"^\d{4}-\d{2}-\d{2}$"
                },
                "amount": {
                    "type": "integer",
                    "description": "금액(원). 0보다 커야 함",
                    "minimum": 1
                },
                "category": {
                    "type": "string",
                    "description": "카테고리",
                    "enum": ["식비", "교통", "쇼핑", "주거", "의료", "교육", "여가", "기타"]
                },
                "memo": {
                    "type": "string",
                    "description": "메모(선택)",
                    "maxLength": 100
                }
            },
            "required": ["date", "amount", "category"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "list_expenses",
        "description": (
            "사용자가 지출을 '조회/목록/최근 내역'으로 보길 원할 때 호출한다. "
            "예: '최근 지출 5개 보여줘', '이번달 내역 보여줘(현재는 최근 N개로 근사)'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "가져올 개수(기본 10, 최대 50)",
                    "minimum": 1,
                    "maximum": 50
                }
            },
            "required": [],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "delete_expense",
        "description": (
            "사용자가 특정 지출을 '삭제'하길 원할 때 호출한다. "
            "단, expense_id가 없으면 먼저 목록을 조회(list_expenses)해 ID를 확인해야 한다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expense_id": {
                    "type": "integer",
                    "description": "삭제할 지출 ID",
                    "minimum": 1
                }
            },
            "required": ["expense_id"],
            "additionalProperties": False
        }
    }
]