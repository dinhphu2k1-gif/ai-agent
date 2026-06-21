"""
========================================================================
OpenSearch Data Dictionary (v1) — bản ghi có trường `id` (UUID)
========================================================================
Dựa trên scripts/seed_data_dictionary.py: cùng dữ liệu GL/CIF, thêm field `id`
cho mỗi document (TABLE | COLUMN | RELATIONSHIP).

OpenSearch `_id` = giá trị `id` trong _source (UUID v4).

Chạy từ thư mục gốc repo:
  python scripts/seed_data_dictionary_1.py

Biến môi trường (tùy chọn):
  OPENSEARCH_INDEX=data_dictionary   # mặc định giống bản gốc; sẽ xóa và tạo lại index
========================================================================
"""

from __future__ import annotations

import copy
import sys
import uuid
from pathlib import Path

# Cho phép import seed_data_dictionary khi chạy: python scripts/seed_data_dictionary_1.py
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

import seed_data_dictionary as base  # noqa: E402

INDEX_NAME = base.INDEX_NAME
EMBEDDING_MODEL_NAME = base.EMBEDDING_MODEL_NAME
EMBEDDING_DIM = base.EMBEDDING_DIM

# Mapping gốc + trường id (keyword, dùng cho filter / filter-service)
INDEX_MAPPING = copy.deepcopy(base.INDEX_MAPPING)
INDEX_MAPPING["mappings"]["properties"] = {
    "id": {"type": "keyword"},
    **INDEX_MAPPING["mappings"]["properties"],
}


def prepare_records_with_ids(records: tuple | list) -> list[dict]:
    """Gán UUID v4 cho mỗi bản ghi; bỏ qua nếu đã có id hợp lệ."""
    prepared: list[dict] = []
    for r in records:
        rec = dict(r)
        existing = rec.get("id")
        if not existing or not str(existing).strip():
            rec["id"] = str(uuid.uuid4())
        else:
            rec["id"] = str(existing).strip()
        prepared.append(rec)
    return prepared


def bulk_index_with_ids(client, index_name: str, records: list, embed_model) -> None:
    """Nạp bulk; _id OpenSearch = trường id trong document."""
    from opensearchpy import helpers

    texts = [base._build_embed_text(r) for r in records]
    print(f"\n🧠 Đang sinh {len(texts)} embeddings với {EMBEDDING_MODEL_NAME}...")
    vectors = embed_model.encode(
        texts, show_progress_bar=True, normalize_embeddings=True
    )
    print(f"✅ Đã sinh xong embeddings (dim={vectors.shape[1]}).")

    actions = [
        {
            "_index": index_name,
            "_id": r["id"],
            "_source": {**r, "description_vector": vec.tolist()},
        }
        for r, vec in zip(records, vectors)
    ]

    print(f"\n📦 Đang nạp {len(actions)} bản ghi (có trường id) vào '{index_name}'...")
    success, errors = helpers.bulk(client, actions, raise_on_error=False)

    if errors:
        print(f"❌ Có {len(errors)} lỗi khi nạp dữ liệu:")
        for err in errors[:5]:
            print(f"   {err}")
    else:
        print(f"✅ Nạp thành công {success} bản ghi (với vectors).")


def verify_ids(client, index_name: str) -> None:
    """Kiểm tra mọi document có trường id và _id khớp id."""
    import time

    time.sleep(2)
    base.verify_index(client, index_name)

    sample = client.search(
        index=index_name,
        body={"size": 3, "query": {"match_all": {}}},
    )
    print("\n🔑 Mẫu trường id (document _id == _source.id):")
    for hit in sample["hits"]["hits"]:
        src = hit["_source"]
        doc_id = hit["_id"]
        field_id = src.get("id", "")
        ok = "✓" if doc_id == field_id else "✗"
        print(
            f"   {ok} _id={doc_id[:36]}...  "
            f"type={src.get('record_type')}  "
            f"table={src.get('table_name', '')}  "
            f"col={src.get('column_name', '') or '-'}"
        )


def main() -> None:
    print("=" * 60)
    print("  OpenSearch Data Dictionary v1 — seed có UUID id")
    print("=" * 60)

    records = prepare_records_with_ids(base.ALL_RECORDS)
    print(f"📋 Chuẩn bị {len(records)} bản ghi, mỗi bản ghi có id (UUID).")

    client = base.create_client()

    print(f"\n🧠 Đang tải mô hình embedding {EMBEDDING_MODEL_NAME}...")
    from sentence_transformers import SentenceTransformer

    embed_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
    print(f"✅ Mô hình embedding sẵn sàng (dim={EMBEDDING_DIM}).")

    if client.indices.exists(index=INDEX_NAME):
        print(f"⚠️  Index '{INDEX_NAME}' đã tồn tại. Đang xóa để tạo lại...")
        client.indices.delete(index=INDEX_NAME)
        import time

        time.sleep(1)

    client.indices.create(index=INDEX_NAME, body=INDEX_MAPPING)
    print(f"✅ Đã tạo index '{INDEX_NAME}' (mapping có trường id).")

    bulk_index_with_ids(client, INDEX_NAME, records, embed_model)
    verify_ids(client, INDEX_NAME)
    base.demo_search(client, INDEX_NAME, embed_model)

    print("\n✅ Hoàn thành! Data Dictionary (v1) đã có trường id trên mọi bản ghi.")
    n_col = len([r for r in records if r.get("record_type") == "COLUMN"])
    n_tbl = len([r for r in records if r.get("record_type") == "TABLE"])
    n_rel = len([r for r in records if r.get("record_type") == "RELATIONSHIP"])
    print(
        f"   Index: {INDEX_NAME}  |  COLUMN: {n_col}  |  TABLE: {n_tbl}  |  "
        f"RELATIONSHIP: {n_rel}  |  Tổng: {len(records)}"
    )
    print(f"   Embedding: {EMBEDDING_MODEL_NAME} (dim={EMBEDDING_DIM})")


if __name__ == "__main__":
    main()
