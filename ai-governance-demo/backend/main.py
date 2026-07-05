"""FastAPI application — AI Governance Demo."""
from __future__ import annotations

import asyncio
import json
import traceback
import uuid
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from database import engine, get_db, Base
from models import User, Role, UserRole
from services.ai_agent import text_to_sql, check_ollama_health
from services.filter_engine import filter_and_execute

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ─── Lifespan ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AI Governance Demo — SeABank",
    description="Demo phân quyền AI Agent: cùng 1 câu hỏi, 3 user nhận kết quả khác nhau",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

from routers import admin
app.include_router(admin.router)

# ─── Schemas ──────────────────────────────────────────────


class ChatRequest(BaseModel):
    question: str
    user_id: str  # username (e.g. "teller_hn")


class UserOut(BaseModel):
    id: str
    username: str
    full_name: str | None
    branch_code: str | None
    role: str | None

    class Config:
        from_attributes = True


# ─── Endpoints ────────────────────────────────────────────

@app.get("/api/health")
async def health():
    ollama_ok = await check_ollama_health()
    return {
        "status": "ok",
        "ollama": "connected" if ollama_ok else "unavailable",
    }


@app.get("/api/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    """List all demo users with their roles."""
    users = db.execute(select(User)).scalars().all()
    result = []
    for u in users:
        role_name = None
        if u.roles:
            role_name = u.roles[0].display_name
        result.append(UserOut(
            id=str(u.id),
            username=u.username,
            full_name=u.full_name,
            branch_code=u.branch_code,
            role=role_name,
        ))
    return result


@app.post("/api/chat")
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """
    SSE streaming chat endpoint.
    Events: thinking → sql → policy → result | error
    """
    # Find user
    user = db.execute(
        select(User).where(User.username == req.user_id)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(404, f"User '{req.user_id}' not found")

    async def event_stream():
        try:
            # Step 1: Thinking
            yield {
                "event": "thinking",
                "data": json.dumps({"message": f"Đang phân tích câu hỏi với tư cách '{user.full_name or user.username}'..."}, ensure_ascii=False),
            }
            await asyncio.sleep(0.3)

            # Step 2: Generate SQL
            yield {
                "event": "thinking",
                "data": json.dumps({"message": "Đang gọi AI để sinh câu truy vấn SQL..."}, ensure_ascii=False),
            }

            sql = await text_to_sql(req.question)

            logger.info(f"User '{req.user_id}' asked: {req.question}")
            logger.info(f"Generated SQL: {sql}")

            if "CANNOT_GENERATE_SQL" in sql:
                yield {
                    "event": "error",
                    "data": json.dumps({"message": "Câu hỏi không liên quan đến dữ liệu ngân hàng."}, ensure_ascii=False),
                }
                return

            yield {
                "event": "sql",
                "data": json.dumps({"sql": sql}, ensure_ascii=False),
            }
            await asyncio.sleep(0.2)

            # Step 3: Filter & Execute
            yield {
                "event": "thinking",
                "data": json.dumps({"message": "Đang kiểm tra quyền truy cập và lọc dữ liệu..."}, ensure_ascii=False),
            }

            result = filter_and_execute(sql, user, db)
            logger.info(f"Rewritten SQL (after filter): {result.rewritten_sql}")

            # Step 4: Policy
            yield {
                "event": "policy",
                "data": json.dumps(result.policy, ensure_ascii=False),
            }
            await asyncio.sleep(0.2)

            # Step 5: Result
            from fastapi.encoders import jsonable_encoder
            clean_rows = jsonable_encoder(result.rows)

            yield {
                "event": "result",
                "data": json.dumps({
                    "columns": result.columns,
                    "rows": clean_rows,
                    "rewritten_sql": result.rewritten_sql,
                    "row_count": len(clean_rows),
                }, ensure_ascii=False),
            }

        except PermissionError as e:
            yield {
                "event": "denied",
                "data": json.dumps({"message": str(e)}, ensure_ascii=False),
            }
        except Exception as e:
            traceback.print_exc()
            yield {
                "event": "error",
                "data": json.dumps({"message": f"Lỗi hệ thống: {str(e)}"}, ensure_ascii=False),
            }

    return EventSourceResponse(event_stream())


# ─── Run ──────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
