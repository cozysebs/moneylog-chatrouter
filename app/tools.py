TOOLS = [
    # transaction-controller (CRUD)
    {
        "type": "function",
        "name": "create_expense",
        "description": (
            "사용자가 지출을 '추가/기록/등록'하길 원할 때 호출한다. "
            "예: '어제 외식 12000원 썼어', '교통비 1500원 추가해줘'."
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
                    "enum": ["외식", "배달", "교통", "쇼핑", "생활", "기타"]
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
        "name": "top_expense_weekday_avg",
        "description": (
            "사용자가 '기간(이번 달/올해 등)별로 요일 중 어느 날에 지출이 가장 큰지' 소비패턴을 확인하려 할 때 호출한다. "
            "각 요일의 평균 지출(요일 총지출 / 해당 기간 내 그 요일의 일수)을 계산한 뒤, 평균이 가장 큰 요일과 평균 금액을 반환한다. "
            "예: '이번 달에 가장 지출이 많은 요일이 언제야?', '올해 요일 중 지출이 제일 큰 날은?'"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "scope": {
                    "type": "string",
                    "enum": ["month", "year"],
                    "description": "기간 단위. month=이번 달(또는 지정 월), year=올해(또는 지정 연)"
                },
                "month": {
                    "type": "string",
                    "description": "scope=month일 때 사용할 월(YYYY-MM). 없으면 현재 월",
                    "pattern": r"^\d{4}-\d{2}$"
                },
                "year": {
                    "type": "string",
                    "description": "scope=year일 때 사용할 연도(YYYY). 없으면 현재 연",
                    "pattern": r"^\d{4}$"
                }
            },
            "required": ["scope"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "delete_expense",
        "description": "사용자가 특정 지출을 삭제하길 원할 때 호출합니다. 삭제는 지출 ID로 가능하며, 날짜 단위('오늘', '어제', '일주일')로도 가능합니다. 날짜 단위가 주어지면 해당 내역을 먼저 보여주고 사용자 확인 후 삭제합니다.",
        "parameters": {
            "type": "object",
            "properties": {
                "expense_id": {
                    "type": "integer",
                    "description": "삭제할 지출 ID. 날짜 단위 삭제를 선택하면 생략 가능.",
                    "minimum": 1
                },
                # "date_range": {
                #     "type": "string",
                #     "description": "삭제할 기간. 예: '오늘', '어제', '지난 7일', '이번 달', '지난 3일'. expense_id가 없는 경우 필수."
                # },
                # "confirm": {
                #     "type": "string",
                #     "description": "유저가 삭제 여부를 확인한 답변. 예: '응', '그래', '아니', '안할래', '네'"
                # }
            },
            "required": [],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "update_expense",
        "description": (
            "사용자가 특정 지출을 '수정/변경'하길 원할 때 호출한다. "
            "예: '방금 지출 금액 12000원을 15000원으로 고쳐줘', '메모를 택시로 바꿔줘'. "
            "단, expense_id가 없으면 먼저 목록을 조회(list_expenses)해 ID를 확인해야 한다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "expense_id": {"type": "integer", "minimum": 1, "description": "수정할 지출 ID"},
                "date": {"type": "string", "pattern": r"^\d{4}-\d{2}-\d{2}$", "description": "날짜(YYYY-MM-DD)"},
                "amount": {"type": "integer", "minimum": 1, "description": "금액(원)"},
                "category": {"type": "string", "enum": ["외식", "배달", "교통", "쇼핑", "생활", "기타"], "description": "카테고리"},
                "memo": {"type": "string", "maxLength": 100, "description": "메모(선택)"}
            },
            "required": ["expense_id", "date", "amount", "category"],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "delete_expense_by_chat",
        "description": (
            "날짜 기준으로 지출을 삭제한다. "
            "금액(amount)과 메모(memo)는 선택 사항이다. "
            "여러 후보가 있으면 서버가 409로 후보 리스트를 반환하며, "
            "챗봇은 번호를 붙여 사용자에게 보여준다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "삭제할 지출의 날짜 (YYYY-MM-DD)",
                    "pattern": r"^\d{4}-\d{2}-\d{2}$"
                },
                "amount": {
                    "type": "integer",
                    "description": "삭제할 지출 금액 (선택)",
                    "minimum": 0
                },
                "memo": {
                    "type": "string",
                    "description": "삭제할 지출 메모 (선택)",
                    "maxLength": 100
                }
            },
            "required": ["date"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "update_expense_by_chat",
        "description": (
            "사용자가 지출을 '수정/변경'하고 싶다고 말하면 무조건 먼저 호출한다. "
            "예: '어제 지출 수정하고 싶어', '지난주 내역 고치고 싶어', "
            "'지출 내역 수정해줘'. "
            "아직 수정할 내용이 없어도 호출한다. "
            "날짜(date), 금액(amount), 메모(memo) 중 하나 이상으로 후보를 찾는다. "
            "후보가 1개 이상이면 서버가 번호가 붙은 후보 목록을 반환한다. "
            "후보가 없으면 '지출내역이 없습니다' 메시지를 반환한다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
            "date": {
                "type": "string",
                "description": "수정할 지출의 날짜 (선택) (YYYY-MM-DD)",
                "pattern": r"^\d{4}-\d{2}-\d{2}$"
            },
            "amount": {
                "type": "integer",
                "description": "수정할 지출 금액 (선택)",
                "minimum": 1
            },
            "memo": {
                "type": "string",
                "description": "수정할 지출 메모 (선택)",
                "maxLength": 100
            }
            },
            "required": [],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "update_expense_by_chat_confirm",
        "description": (
            "이전에 반환된 지출 수정 후보 중 하나를 선택해 수정한다. "
            "candidateIndex는 1부터 시작한다. "
            "newData에는 수정할 필드만 포함한다. "
            "수정 가능한 필드는 date, amount, memo 뿐이다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
            "candidateIndex": {
                "type": "integer",
                "description": "수정할 후보 번호 (1부터 시작)",
                "minimum": 1
            },
            "newData": {
                "type": "object",
                "properties": {
                "date": {
                    "type": "string",
                    "pattern": r"^\d{4}-\d{2}-\d{2}$",
                    "description": "새 날짜 (선택)"
                },
                "amount": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "새 금액 (선택)"
                },
                "memo": {
                    "type": "string",
                    "maxLength": 100,
                    "description": "새 메모 (선택)"
                }
                },
                "required": [],
                "additionalProperties": False
            }
            },
            "required": ["candidateIndex", "newData"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "create_income",
        "description": (
            "사용자가 수입을 '추가/기록/등록'하길 원할 때 호출한다. "
            "예: '월급 300만원 들어왔어', '용돈 5만원 받았어'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
            "date": {
                "type": "string",
                "description": "날짜(YYYY-MM-DD)",
                "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
            },
            "amount": {
                "type": "integer",
                "description": "금액(원). 0보다 커야 함",
                "minimum": 1
            },
            "category": {
                "type": "string",
                "enum": ["월급","용돈","부수입","기타"]
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
        "name": "list_incomes",
        "description": (
            "사용자가 수입을 '조회/목록/최근 내역'으로 보길 원할 때 호출한다. "
            "예: '최근 수입 5개 보여줘', '이번달 수입 내역 보여줘'."
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
        "name": "delete_income_by_chat",
        "description": (
            "날짜 기준으로 수입을 삭제한다. "
            "금액(amount)과 메모(memo)는 선택 사항이다. "
            "여러 후보가 있으면 서버가 409로 후보 리스트를 반환하며, "
            "챗봇은 번호를 붙여 사용자에게 보여준다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
            "date": {
                "type": "string",
                "description": "삭제할 수입의 날짜 (YYYY-MM-DD)",
                "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
            },
            "amount": {
                "type": "integer",
                "description": "삭제할 수입 금액 (선택)",
                "minimum": 0
            },
            "memo": {
                "type": "string",
                "description": "삭제할 수입 메모 (선택)",
                "maxLength": 100
            }
            },
            "required": ["date"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "update_income_by_chat",
        "description": (
            "사용자가 수입을 '수정/변경'하고 싶다고 말하면 무조건 먼저 호출한다. "
            "예: '어제 수입 수정하고 싶어', '지난달 월급 고치고 싶어'. "
            "아직 수정할 내용이 없어도 호출한다. "
            "날짜(date), 금액(amount), 메모(memo) 중 하나 이상으로 후보를 찾는다. "
            "후보가 1개 이상이면 서버가 번호가 붙은 후보 목록을 반환한다. "
            "후보가 없으면 '수입내역이 없습니다' 메시지를 반환한다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
            "date": {
                "type": "string",
                "description": "수정할 수입의 날짜 (선택) (YYYY-MM-DD)",
                "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
            },
            "amount": {
                "type": "integer",
                "description": "수정할 수입 금액 (선택)",
                "minimum": 1
            },
            "memo": {
                "type": "string",
                "description": "수정할 수입 메모 (선택)",
                "maxLength": 100
            }
            },
            "required": [],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "update_income_by_chat_confirm",
        "description": (
            "이전에 반환된 수입 수정 후보 중 하나를 선택해 수정한다. "
            "candidateIndex는 1부터 시작한다. "
            "newData에는 수정할 필드만 포함한다. "
            "수정 가능한 필드는 date, amount, memo 뿐이다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
            "candidateIndex": {
                "type": "integer",
                "description": "수정할 후보 번호 (1부터 시작)",
                "minimum": 1
            },
            "newData": {
                "type": "object",
                "properties": {
                "date": {
                    "type": "string",
                    "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
                    "description": "새 날짜 (선택)"
                },
                "amount": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "새 금액 (선택)"
                },
                "memo": {
                    "type": "string",
                    "maxLength": 100,
                    "description": "새 메모 (선택)"
                }
                },
                "required": [],
                "additionalProperties": False
            }
            },
            "required": ["candidateIndex", "newData"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "create_expense_batch",
        "description": (
            "사용자가 여러 지출을 한 번에 등록하려고 할 때 호출한다. "
            "예: '어제 지출 3개 한꺼번에 등록해줘', "
            "'외식 12000원, 교통 1500원, 커피 4500원 등록해줘'. "
            "각 항목은 실패해도 전체가 롤백되지 않으며, "
            "성공/실패 결과를 함께 반환한다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "transactions": {
                    "type": "array",
                    "description": "등록할 지출 목록",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
                                "description": "날짜(YYYY-MM-DD)"
                            },
                            "amount": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "금액(원)"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["외식", "배달", "교통", "쇼핑", "생활", "기타"]
                            },
                            "memo": {
                                "type": "string",
                                "maxLength": 100,
                                "description": "메모(선택)"
                            }
                        },
                        "required": ["date", "amount", "category"],
                        "additionalProperties": False
                    },
                    "minItems": 1
                }
            },
            "required": ["transactions"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "create_income_batch",
        "description": (
            "사용자가 여러 수입을 한 번에 등록하려고 할 때 호출한다. "
            "예: '월급이랑 보너스 같이 등록해줘', "
            "'1월 수입 2개 한 번에 추가해줘'. "
            "각 항목은 개별 처리되며 실패 내역도 함께 반환된다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "transactions": {
                    "type": "array",
                    "description": "등록할 수입 목록",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "pattern": "^\\d{4}-\\d{2}-\\d{2}$",
                                "description": "날짜(YYYY-MM-DD)"
                            },
                            "amount": {
                                "type": "integer",
                                "minimum": 1,
                                "description": "금액(원)"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["월급","용돈","부수입","기타"]
                            },
                            "memo": {
                                "type": "string",
                                "maxLength": 100,
                                "description": "메모(선택)"
                            }
                        },
                        "required": ["date", "amount", "category"],
                        "additionalProperties": False
                    },
                    "minItems": 1
                }
            },
            "required": ["transactions"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "get_top_expense_category",
        "description": (
            "사용자가 특정 기간 동안 가장 많이 지출한 카테고리를 알고 싶어할 때 호출한다. "
            "예: '이번 달에 제일 많이 쓴 카테고리 뭐야?', "
            "'지난주에 어디에 돈 제일 많이 썼어?'. "
            "지출 전용이며 수입은 포함하지 않는다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "조회 기간",
                    "enum": ["day","week", "month","year"]
                },
                "date": {
                    "type": "string",
                    "description": (
                        "기준 날짜(YYYY-MM-DD). "
                        "없으면 서버에서 오늘 날짜를 기준으로 계산한다."
                    ),
                    "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                }
            },
            "required": ["period"],
            "additionalProperties": False
        }
    },


    # summary-controller (READ)
    {
        "type": "function",
        "name": "get_expense_summary",
        "description": (
            "사용자가 지출 합계를 알고 싶어할 때 호출한다. "
            "예: '이번 달 지출 총액 얼마야?', "
            "'지난주에 돈 얼마나 썼어?', "
            "'오늘 지출 합계 알려줘'. "
            "period는 day/week/month/year 중 하나다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "조회 기간",
                    "enum": ["day", "week", "month", "year"]
                },
                "date": {
                    "type": "string",
                    "description": (
                        "기준 날짜(YYYY-MM-DD). "
                        "없으면 서버에서 오늘 날짜를 기준으로 계산한다."
                    ),
                    "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                }
            },
            "required": ["period"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "get_income_summary",
        "description": (
            "사용자가 수입 합계를 알고 싶어할 때 호출한다. "
            "예: '이번 달 수입 총액 얼마야?', "
            "'올해 수입 얼마나 벌었어?', "
            "'지난주 수입 합계 알려줘'. "
            "period는 day/week/month/year 중 하나다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "조회 기간",
                    "enum": ["day", "week", "month", "year"]
                },
                "date": {
                    "type": "string",
                    "description": (
                        "기준 날짜(YYYY-MM-DD). "
                        "없으면 서버에서 오늘 날짜를 기준으로 계산한다."
                    ),
                    "pattern": "^\\d{4}-\\d{2}-\\d{2}$"
                }
            },
            "required": ["period"],
            "additionalProperties": False
        }
    },

    # reply-controller (CRUD)
    {
        "type": "function", 
        "name": "create_reply", # 1) POST: 댓글 작성
        "description": (
            "사용자가 게시글에 댓글을 '작성/등록'하길 원할 때 호출한다. "
            "예: '게시글 12번에 댓글로 \"좋아요\" 남겨줘'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "bno": {"type": "integer", "minimum": 1, "description": "게시글 ID(board number)"},
                "content": {"type": "string", "minLength": 1, "maxLength": 3000, "description": "댓글 내용"}
            },
            "required": ["bno", "content"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "list_replies", # 2) GET: 게시글 댓글 목록(페이지는 1 고정, size는 최소 10이라 limit→size로 매핑)
        "description": (
            "사용자가 특정 게시글의 댓글을 '조회/목록'으로 보길 원할 때 호출한다. "
            "예: '게시글 12번 댓글 보여줘', '댓글 10개만 보여줘'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "bno": {"type": "integer", "minimum": 1, "description": "게시글 ID(board number)"},
                "limit": {"type": "integer", "minimum": 10, "maximum": 20, "description": "가져올 개수(기본 10, 최대 20)"}
            },
            "required": ["bno"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "delete_reply", # 3) DELETE: 댓글 삭제(soft delete)
        "description": (
            "사용자가 특정 댓글을 '삭제'하길 원할 때 호출한다. "
            "단, reply_id가 없으면 먼저 list_replies로 ID를 확인해야 한다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "reply_id": {"type": "integer", "minimum": 1, "description": "삭제할 댓글 ID"}
            },
            "required": ["reply_id"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "update_reply", # 4) UPDATE: 댓글 수정
        "description": (
            "사용자가 댓글을 수정/변경하길 원할 때 호출한다. "
            "예: '댓글 15번 내용을 \"감사합니다\"로 바꿔줘'. "
            "reply_id가 없으면 list_replies로 먼저 ID를 확인해야 한다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
            "reply_id": {"type": "integer", "minimum": 1, "description": "수정할 댓글 ID"},
            "content": {"type": "string", "minLength": 1, "maxLength": 3000, "description": "수정할 댓글 내용"}
            },
            "required": ["reply_id", "content"],
            "additionalProperties": False
        }
    },

    # notice-controller (CRUD)
    {
        "type": "function",
        "name": "create_notice",    # POST: 공지 작성
        "description": "공지사항을 작성한다. 예: '공지 제목은 ... 내용은 ... 으로 공지 올려줘'.",
        "parameters": {
            "type": "object",
            "properties": {
            "title": {"type": "string", "minLength": 1, "maxLength": 200},
            "content": {"type": "string", "minLength": 1, "maxLength": 5000},
            "imageUrl": {"type": "string", "maxLength": 500}
            },
            "required": ["title", "content"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "list_notices",     # GET: 공지 목록 (페이로드 줄이기 위해 limit 10~20)
        "description": "공지사항 목록을 조회한다. 예: '공지사항 10개 보여줘'.",
        "parameters": {
            "type": "object",
            "properties": {
            "limit": {"type": "integer", "minimum": 10, "maximum": 20, "description": "가져올 개수(기본 10, 최대 20)"}
            },
            "required": [],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "delete_notice",     # DELETE: 공지 삭제
        "description": "공지사항을 삭제한다. notice_id가 없으면 list_notices로 먼저 ID를 확인해야 한다.",
        "parameters": {
            "type": "object",
            "properties": {
            "notice_id": {"type": "integer", "minimum": 1}
            },
            "required": ["notice_id"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "update_notice",    # UPDATE: 공지 수정
        "description": (
            "공지사항을 수정한다. 예: '공지 10번 제목을 ...로, 내용을 ...로 수정해줘'. "
            "notice_id가 없으면 list_notices로 먼저 ID를 확인해야 한다."
        ),
        "parameters": {
            "type": "object",
            "properties": {
            "notice_id": {"type": "integer", "minimum": 1, "description": "수정할 공지 ID"},
            "title": {"type": "string", "minLength": 1, "maxLength": 200, "description": "공지 제목"},
            "content": {"type": "string", "minLength": 1, "maxLength": 5000, "description": "공지 내용"},
            "imageUrl": {"type": "string", "maxLength": 500, "description": "이미지 URL(선택)"}
            },
            "required": ["notice_id", "title", "content"],
            "additionalProperties": False
        }
    },

    # member-controller (CRUD)
    {
        "type": "function",
        "name": "list_members",
        "description": "회원 목록을 조회한다(관리자 전용). 예: '회원 10명 보여줘'.",
        "parameters": {
            "type": "object",
            "properties": {
            "limit": {"type": "integer", "minimum": 10, "maximum": 20, "description": "가져올 개수(기본 10, 최대 20)"}
            },
            "required": [],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "verify_password",
        "description": "로그인한 사용자의 비밀번호가 맞는지 검증한다. 예: '내 비밀번호 확인해줘'.",
        "parameters": {
            "type": "object",
            "properties": {
            "password": {"type": "string", "minLength": 1, "maxLength": 200}
            },
            "required": ["password"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "delete_member",
        "description": "회원 계정을 삭제한다(본인 또는 관리자만 가능). 예: '내 계정 삭제해줘'.",
        "parameters": {
            "type": "object",
            "properties": {
            "member_id": {"type": "integer", "minimum": 1}
            },
            "required": ["member_id"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "update_member_info",
        "description": (
            "로그인한 사용자의 회원 정보를 수정한다. "
            "nickname 또는 password 중 최소 1개를 제공해야 한다. "
            "예: '닉네임을 세븐으로 바꿔줘', '비밀번호를 변경해줘'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
            "nickname": {"type": "string", "minLength": 1, "maxLength": 50, "description": "새 닉네임(선택)"},
            "password": {"type": "string", "minLength": 1, "maxLength": 200, "description": "새 비밀번호(선택)"}
            },
            "required": [],
            "additionalProperties": False
        }
    },

    # budget-controller (CRUD) -> Delete는 없고 patch로 예산 증감만 가능함
    {
        "type": "function",
        "name": "create_budget",
        "description": "예산을 생성(등록)한다. 예: '2026년 1월 예산을 50만원으로 등록해줘'.",
        "parameters": {
            "type": "object",
            "properties": {
            "year": {"type": "integer", "minimum": 2000, "maximum": 2100},
            "month": {"type": "integer", "minimum": 1, "maximum": 12},
            "limitAmount": {"type": "integer", "minimum": 0, "maximum": 200000000},
            "usedAmount": {"type": "integer", "minimum": 0, "maximum": 200000000}
            },
            "required": ["year", "month", "limitAmount"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "list_budgets",
        "description": "특정 회원(mid)의 예산 목록을 조회한다. 예: 'mid 3의 예산 10개 보여줘'.",
        "parameters": {
            "type": "object",
            "properties": {
            "mid": {"type": "integer", "minimum": 1},
            "limit": {"type": "integer", "minimum": 10, "maximum": 20}
            },
            "required": ["mid"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "adjust_budget_limit",
        "description": (
            "로그인한 사용자의 월 예산 한도를 증감(delta)한다. "
            "예: '이번 달 예산을 5만원 올려줘', '예산 2만원 줄여줘'. "
            "delta는 +면 증가, -면 감소."
        ),
        "parameters": {
            "type": "object",
            "properties": {
            "mid": {"type": "integer", "minimum": 1, "description": "대상 회원 ID(보통 본인)"},
            "delta": {"type": "integer", "minimum": -200000000, "maximum": 200000000, "description": "예산 증감액(+/-)"}
            },
            "required": ["mid", "delta"],
            "additionalProperties": False
        }
    },

    # board-controller (CRUD)
    {
        "type": "function",
        "name": "create_board",
        "description": "게시글을 작성한다. 예: '제목은 ... 내용은 ... 으로 게시글 올려줘'.",
        "parameters": {
            "type": "object",
            "properties": {
            "title": {"type": "string", "minLength": 1, "maxLength": 200},
            "content": {"type": "string", "minLength": 1, "maxLength": 5000},
            "imageUrl": {"type": "string", "maxLength": 500}
            },
            "required": ["title", "content"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "get_board",
        "description": "게시글 단건을 조회한다. 예: '게시글 10번 보여줘'.",
        "parameters": {
            "type": "object",
            "properties": {
            "board_id": {"type": "integer", "minimum": 1}
            },
            "required": ["board_id"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "delete_board",
        "description": "게시글을 삭제한다(본인 글만). 예: '게시글 10번 삭제해줘'.",
        "parameters": {
            "type": "object",
            "properties": {
            "board_id": {"type": "integer", "minimum": 1}
            },
            "required": ["board_id"],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "list_boards",
        "description": "게시글 목록을 조회한다. 예: '게시글 10개 보여줘', '게시글 검색어: 투자 로 찾아줘'.",
        "parameters": {
            "type": "object",
            "properties": {
            "page": {"type": "integer", "minimum": 1, "maximum": 1000, "description": "페이지(1부터)"},
            "limit": {"type": "integer", "minimum": 10, "maximum": 20, "description": "가져올 개수(10~20)"},
            "keyword": {"type": "string", "maxLength": 100, "description": "검색어(선택)"},
            "types": {
                "type": "string",
                "maxLength": 10,
                "description": "검색 타입(선택). 예: 'tc' (title+content). PageRequestDTO types 규칙에 맞게 사용."
            }
            },
            "required": [],
            "additionalProperties": False
        }
    },
    {
        "type": "function",
        "name": "update_board",
        "description": "게시글을 수정한다(본인 글만). 예: '게시글 3번 제목/내용 수정해줘'.",
        "parameters": {
            "type": "object",
            "properties": {
            "board_id": {"type": "integer", "minimum": 1},
            "title": {"type": "string", "minLength": 1, "maxLength": 200},
            "content": {"type": "string", "minLength": 1, "maxLength": 5000},
            "imageUrl": {"type": "string", "maxLength": 500}
            },
            "required": ["board_id", "title", "content"],
            "additionalProperties": False
        }
    },

    # authentication-controller (only sign-in)
    {
        "type": "function",
        "name": "sign_in",
        "description": "아이디/비밀번호로 로그인(JWT 발급). 예: '아이디 a, 비밀번호 b로 로그인해줘'.",
        "parameters": {
            "type": "object",
            "properties": {
                "username": {"type": "string", "minLength": 1, "maxLength": 50},
                "password": {"type": "string", "minLength": 1, "maxLength": 200}
            },
            "required": ["username", "password"],
            "additionalProperties": False
        }
    }




]