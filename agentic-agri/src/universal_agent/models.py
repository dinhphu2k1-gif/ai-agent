"""
Factory để khởi tạo các models (LLM) theo cấu hình của hệ thống.
"""

import os
from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel

# Nạp các thư viện của từng hãng
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama

load_dotenv()


class LLMFactory:
    """Factory class tạo LLM instances theo provider."""

    @staticmethod
    def create(provider: str, model_name: str, temperature: float, base_url: str, api_key: str = "EMPTY") -> BaseChatModel:
        """Tạo instance BaseChatModel tương ứng với cấu hình."""
        provider = provider.lower().strip()

        if provider == "vllm":
            return ChatOpenAI(
                model=model_name,
                temperature=temperature,
                api_key=api_key,
                base_url=base_url,
            )
        elif provider == "google":
            return ChatGoogleGenerativeAI(
                model=model_name, temperature=temperature, api_key=api_key
            )
        elif provider == "ollama":
            return ChatOllama(
                model=model_name,
                temperature=temperature,
                base_url=base_url,
            )
        else:
            raise ValueError(f"Provider '{provider}' không được hỗ trợ.")

    @classmethod
    def create_supervisor(cls) -> BaseChatModel:
        """Tạo LLM chuyên biệt cho Supervisor layer (yêu cầu reason/logic cao)."""
        vllm_url = os.environ.get("SUPERVISOR_API_URL", "http://localhost:8000/v1")
        vllm_key = os.environ.get("SUPERVISOR_API_KEY", "EMPTY")
        return cls.create(
            provider=os.environ.get("SUPERVISOR_PROVIDER", "vllm"),
            model_name=os.environ.get("SUPERVISOR_MODEL", "Qwen/Qwen2.5-72B-Instruct"),
            temperature=float(os.environ.get("SUPERVISOR_TEMPERATURE", 0.0)),
            base_url=vllm_url,
            api_key=vllm_key,
        )

    @classmethod
    def create_worker(cls) -> BaseChatModel:
        """Tạo LLM chuyên biệt cho Worker agents (yêu cầu sinh text/code)."""
        return cls.create(
            provider=os.environ.get("WORKER_PROVIDER", "vllm"),
            model_name=os.environ.get("WORKER_MODEL", "Qwen/Qwen2.5-7B-Instruct"),
            temperature=float(os.environ.get("WORKER_TEMPERATURE", 0.1)),
            api_key=os.environ.get("WORKER_API_KEY", "EMPTY"),
            base_url=os.environ.get("WORKER_API_URL", "http://localhost:8000/v1"),
        )

    @classmethod
    def create_sql_writer(cls) -> BaseChatModel:
        """Tạo LLM dành riêng cho SQL writer, ưu tiên vLLM để sinh và sửa query."""
        base_url = os.environ.get("SQL_WRITER_API_URL", "http://localhost:8000/v1")
        api_key = os.environ.get("SQL_WRITER_API_KEY", "EMPTY")
        return cls.create(
            provider=os.environ.get("SQL_WRITER_PROVIDER", "ollama"),
            model_name=os.environ.get("SQL_WRITER_MODEL", "qwen2.5-coder:7b"),
            temperature=float(os.environ.get("SQL_WRITER_TEMPERATURE", 0.0)),
            base_url=base_url,
            api_key=api_key,
        )


# --- KHỞI TẠO CÁC LLM INSTANCE SẴN ĐỂ IMPORT (Backward Compatible) ---
llm = LLMFactory.create_supervisor()
worker_llm = LLMFactory.create_worker()
sql_writer_llm = LLMFactory.create_sql_writer()
