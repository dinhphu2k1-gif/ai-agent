"""
Nodes cho Metadata Agent Sub-Graph.

Bao gồm: query_analyzer, opensearch_retriever, result_synthesizer.
"""

import json

from langchain_core.runnables import RunnableConfig

from ..models import worker_llm
from ..utils import get_text_content, strip_markdown_json
from .metadata_retrieval_client import (
    create_metadata_retrieval_client,
    resolve_metadata_user_context,
)
from .neo4j_expansion import expand_tables_from_neo4j
from .opensearch_client import OpenSearchClient
from .prompts import METADATA_QUERY_ANALYSIS_PROMPT, METADATA_SYNTHESIS_PROMPT
from .state import MetadataState


def _collect_seed_tables(all_hits: list[dict], target_tables: list[str]) -> list[str]:
    tables = list(target_tables)
    for hit in all_hits:
        tbl = hit.get("_source", {}).get("table_name", "")
        if tbl and tbl != "_RELATIONSHIP" and tbl not in tables:
            tables.append(tbl)
    return tables


def _tables_with_columns(hits: list[dict]) -> set[str]:
    return {
        hit.get("_source", {}).get("table_name", "")
        for hit in hits
        if hit.get("_source", {}).get("record_type") == "COLUMN"
        and hit.get("_source", {}).get("table_name")
    }


def query_analyzer_node(state: MetadataState) -> dict:
    """Phân tích yêu cầu người dùng → sinh search strategy (JSON)."""
    user_input = state.get("user_input", "")
    log = state.get("investigation_log_input", "")

    prompt = f"""
    {METADATA_QUERY_ANALYSIS_PROMPT}

    --- DỮ LIỆU ĐẦU VÀO ---
    USER INPUT: {user_input}
    INVESTIGATION LOG: {log}
    """

    response = worker_llm.invoke(prompt)
    raw_content = strip_markdown_json(get_text_content(response))

    try:
        strategy = json.loads(raw_content)
    except json.JSONDecodeError as e:
        print(f"⚠️ [Query Analyzer] JSON parse error: {e}")
        strategy = {
            "semantic_query": user_input,
            "keywords": user_input.split()[:5],
            "target_tables": [],
            "record_types": ["TABLE", "COLUMN"],
        }

    print(f"🔍 [Query Analyzer] Strategy: {json.dumps(strategy, ensure_ascii=False, indent=2)}")
    return {"search_strategy": strategy}


def opensearch_retriever_node(
    state: MetadataState, config: RunnableConfig | None = None
) -> dict:
    """Thực thi metadata search (filter-service/OpenSearch) + Neo4j relationship expansion."""
    strategy = state.get("search_strategy", {})
    user_id, thread_id = resolve_metadata_user_context(state, config)
    client = create_metadata_retrieval_client(user_id, thread_id)
    format_results = getattr(client, "format_search_results", OpenSearchClient.format_search_results)

    semantic_query = strategy.get("semantic_query", "")
    keywords = strategy.get("keywords", [])
    target_tables = strategy.get("target_tables", [])

    all_hits: list[dict] = []

    if semantic_query:
        try:
            hits = client.hybrid_search(semantic_query, size=10)
            all_hits.extend(hits)
            print(f"📡 [Retriever] Hybrid search (userId={user_id}): {len(hits)} kết quả")
        except Exception as e:
            print(f"⚠️ [Retriever] Hybrid search lỗi: {e}")

    keyword_query = " ".join(keywords[:3])
    if keyword_query and not target_tables:
        try:
            kw_hits = client.search_by_keyword(keyword_query, size=5)
            all_hits.extend(kw_hits)
            print(f"📡 [Retriever] Keyword search: {len(kw_hits)} kết quả")
        except Exception as e:
            print(f"⚠️ [Retriever] Keyword search lỗi: {e}")

    seed_tables = _collect_seed_tables(all_hits, target_tables)
    neo4j_join_context = ""
    expanded_tables = seed_tables

    if seed_tables:
        expanded_tables, neo4j_join_context = expand_tables_from_neo4j(seed_tables[:5])
        path_count = neo4j_join_context.count("[RELATIONSHIP]") if neo4j_join_context else 0
        print(
            f"📡 [Retriever] Neo4j expanded: {len(expanded_tables)} tables, "
            f"{path_count} relationship blocks"
        )

    tables_with_columns = _tables_with_columns(all_hits)
    for table in expanded_tables:
        if table in tables_with_columns:
            continue
        try:
            table_meta = client.get_table_metadata(table)
            all_hits.extend(table_meta)

            columns = client.get_table_schema(table)
            all_hits.extend(columns)
            tables_with_columns.add(table)

            print(
                f"📡 [Retriever] Schema '{table}': "
                f"{len(table_meta)} TABLE + {len(columns)} COLUMN records"
            )
        except Exception as e:
            print(f"⚠️ [Retriever] Lấy schema '{table}' lỗi: {e}")

    seen_ids: set[str] = set()
    unique_hits: list[dict] = []
    for hit in all_hits:
        doc_id = hit.get("_id", "")
        if doc_id not in seen_ids:
            seen_ids.add(doc_id)
            unique_hits.append(hit)

    list_tables = [
        hit.get("_source", {}).get("table_name", "") for hit in unique_hits
    ]
    list_tables.extend(expanded_tables)
    list_tables = list({t for t in list_tables if t and t != "_RELATIONSHIP"})

    formatted = format_results(unique_hits)
    if neo4j_join_context:
        formatted = f"{formatted}\n\n{neo4j_join_context}"

    print(f"📦 [Retriever] Tổng: {len(unique_hits)} kết quả unique (sau dedup)")
    print(f"List Tables: {list_tables}")
    print(f"Expanded Tables: {expanded_tables}")
    return {
        "raw_results": formatted,
        "list_tables": list_tables,
        "neo4j_join_context": neo4j_join_context,
        "expanded_tables": expanded_tables,
        "metadata_hits": unique_hits,
    }

def result_synthesizer_node(state: MetadataState) -> dict:
    """Tổng hợp kết quả search thành schema có cấu trúc cho SQL Writer."""
    user_input = state.get("user_input", "")
    raw_results = state.get("raw_results", "")
    neo4j_join_context = state.get("neo4j_join_context") or ""

    if not raw_results or raw_results == "Không tìm thấy kết quả nào trong Data Dictionary.":
        return {
            "synthesized_schema": "Không tìm thấy metadata phù hợp trong Data Dictionary. "
            "Cần hỏi lại người dùng để làm rõ yêu cầu."
        }

    prompt = METADATA_SYNTHESIS_PROMPT.format(
        search_results=raw_results,
        user_input=user_input,
        neo4j_join_context=neo4j_join_context or "Không có.",
    )

    response = worker_llm.invoke(prompt)
    synthesized = get_text_content(response).strip()

    print(f"✅ [Synthesizer] Đã tổng hợp schema ({len(synthesized)} ký tự)")

    return {"synthesized_schema": synthesized}
