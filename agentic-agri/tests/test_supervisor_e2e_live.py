import os
import sys
import uuid
from unittest.mock import patch

sys.path.insert(0, "F:/data/src/agentic-agri/src")
sys.path.insert(0, "F:/data/src/agentic-agri")

from langgraph.checkpoint.memory import MemorySaver

from tests.llm_cache_utils import CachedInvokeClient, should_run_live_e2e
from universal_agent.models import llm
from universal_agent.supervisor.graph import SupervisorGraph

def _skip_if_disabled():
    if not should_run_live_e2e():
        raise RuntimeError(
            "Set RUN_LIVE_SUPERVISOR_E2E=1 to run live supervisor end-to-end tests with cached external responses."
        )


def _build_test_app():
    return SupervisorGraph().compile(checkpointer=MemorySaver())


def _base_env():
    os.environ.setdefault("PG_HOST", "192.168.2.161")
    os.environ.setdefault("PG_PORT", "5432")
    os.environ.setdefault("PG_USER", "admin")
    os.environ.setdefault("PG_PASSWORD", "password123")
    os.environ.setdefault("PG_DATABASE", "my_database")
    os.environ.setdefault("SQL_EXECUTOR_DIALECT", "postgresql")


def run_supervisor_e2e_account_query():
    _skip_if_disabled()
    _base_env()

    planner_cache = CachedInvokeClient(llm, "supervisor_planner")

    app = _build_test_app()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    current_input = {
        "user_input": "Cho tôi 5 tài khoản đầu tiên gồm mã và tên tài khoản",
        "investigation_log": ["Nhận yêu cầu: Cho tôi 5 tài khoản đầu tiên gồm mã và tên tài khoản"],
    }

    with patch("universal_agent.supervisor.nodes.llm", planner_cache):
        app.invoke(current_input, config=config)
        snapshot = app.get_state(config)

    return snapshot.values


def run_supervisor_e2e_customer_account_join_query():
    _skip_if_disabled()
    _base_env()

    planner_cache = CachedInvokeClient(llm, "supervisor_planner")

    app = _build_test_app()
    config = {"configurable": {"thread_id": str(uuid.uuid4())}}
    current_input = {
        "user_input": "Cho tôi 5 khách hàng đầu tiên và mã tài khoản GL tương ứng",
        "investigation_log": ["Nhận yêu cầu: Cho tôi 5 khách hàng đầu tiên và mã tài khoản GL tương ứng"],
    }

    with patch("universal_agent.supervisor.nodes.llm", planner_cache):
        app.invoke(current_input, config=config)
        snapshot = app.get_state(config)

    return snapshot.values


def test_supervisor_e2e_account_query_live():
    values = run_supervisor_e2e_account_query()

    assert values["generated_sql"].upper().startswith("SELECT")
    assert "gl_accounts" in values["generated_sql"].lower()
    assert values["sql_execution_error"] is None
    assert "Rows:" in values["final_output"]
    assert "account_code" in values["sql_result_preview"].lower()


def test_supervisor_e2e_customer_account_join_live():
    values = run_supervisor_e2e_customer_account_join_query()

    assert values["generated_sql"].upper().startswith("SELECT")
    assert "join" in values["generated_sql"].lower()
    assert values["sql_execution_error"] is None
    assert "cif_number" in values["sql_result_preview"].lower()
    assert "account_code" in values["sql_result_preview"].lower()
