"""AI Agent — Convert natural language questions to SQL via Ollama."""
from __future__ import annotations

import os
import re
import httpx
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11435")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

SYSTEM_PROMPT = """Bạn là chuyên gia SQL cho hệ thống Core Banking ngân hàng SeABank.
Database sử dụng PostgreSQL. Schema: core_banking.

CÁC BẢNG HIỆN CÓ:

1. core_banking.customers
   - customer_id (SERIAL, PRIMARY KEY)
   - full_name (VARCHAR) — Họ tên khách hàng
   - phone_number (VARCHAR) — Số điện thoại
   - id_number (VARCHAR) — Số CMND/CCCD
   - branch_code (VARCHAR) — Mã chi nhánh (HN, HCM, DN)
   - balance (NUMERIC) — Số dư tài khoản (VND)

2. core_banking.transactions
   - txn_id (SERIAL, PRIMARY KEY)
   - customer_id (INT, FK → customers) — Mã khách hàng
   - amount (NUMERIC) — Số tiền giao dịch (VND)
   - txn_type (VARCHAR) — Loại: DEPOSIT, WITHDRAW, TRANSFER
   - txn_date (DATE) — Ngày giao dịch
   - branch_code (VARCHAR) — Chi nhánh thực hiện

QUY TẮC:
- Chỉ sinh một câu SELECT duy nhất.
- Luôn dùng schema prefix: core_banking.customers, core_banking.transactions
- KHÔNG thêm LIMIT trừ khi người dùng yêu cầu.
- KHÔNG giải thích. CHỈ trả về câu SQL thuần.
- Nếu câu hỏi không liên quan đến dữ liệu, trả về: CANNOT_GENERATE_SQL"""


async def text_to_sql(question: str) -> str:
    """Call Ollama to generate SQL from a natural language question."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": f"{SYSTEM_PROMPT}\n\nCâu hỏi: {question}",
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 512,
        },
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
        resp.raise_for_status()
        data = resp.json()

    raw = data.get("response", "").strip()

    # Extract SQL from response (may be wrapped in ```sql ... ```)
    sql_match = re.search(r"```(?:sql)?\s*(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    if sql_match:
        return sql_match.group(1).strip()

    # Check if response starts with SELECT
    select_match = re.search(r"(SELECT\s+.+)", raw, re.IGNORECASE | re.DOTALL)
    if select_match:
        return select_match.group(1).strip().rstrip(";") + ";"

    return raw


async def check_ollama_health() -> bool:
    """Check if Ollama is running and the model is available."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                return any(OLLAMA_MODEL in m for m in models)
    except Exception:
        pass
    return False
