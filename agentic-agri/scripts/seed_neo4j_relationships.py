"""
========================================================================
Neo4j Relationship Graph Loader – Table JOIN Paths
========================================================================
Mô tả   : Khởi tạo graph database Neo4j để lưu trữ mối quan hệ giữa
          các bảng (FK relationships, cross-domain paths).
          Dữ liệu này được sử dụng bởi SQL Writer Agent để:
          1. Tính toán đường dẫn JOIN ngắn nhất
          2. Gợi ý JOIN chains
          3. Validate table access paths
Phiên bản: Neo4j 5.0+
Tác giả  : SQL Writer Agent Development
========================================================================
"""

import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

from metadata_utils import infer_table_category, load_metadata_bundle

load_dotenv()

METADATA = load_metadata_bundle()

# Neo4j connection config
NEO4J_CONFIG = {
    "uri": os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
    "user": os.environ.get("NEO4J_USER", "neo4j"),
    "password": os.environ.get("NEO4J_PASSWORD", "password"),
}


def create_driver():
    """Tạo Neo4j driver."""
    try:
        driver = GraphDatabase.driver(
            NEO4J_CONFIG["uri"],
            auth=(NEO4J_CONFIG["user"], NEO4J_CONFIG["password"]),
        )
        driver.verify_connectivity()
        print(f"✅ Kết nối Neo4j thành công: {NEO4J_CONFIG['uri']}")
        return driver
    except Exception as e:
        print(f"⚠️  Lỗi kết nối Neo4j: {e}")
        raise


def clear_graph(driver):
    """Xóa toàn bộ graph hiện tại."""
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
    print("🗑️  Xóa graph cũ")


def create_tables(driver):
    """Tạo nodes cho các bảng từ metadata."""
    with driver.session() as session:
        for table in METADATA.tables:
            session.run(
                """
                MERGE (t:Table {name: $name})
                SET t.schema_name = $schema_name,
                    t.domain = $domain,
                    t.type = $type,
                    t.business_name = $business_name,
                    t.description = $description,
                    t.table_purpose = $table_purpose,
                    t.related_tables = $related_tables,
                    t.created_at = datetime()
                """,
                name=table.table_name,
                schema_name=table.schema_name,
                domain=table.domain_name,
                type=infer_table_category(table),
                business_name=table.business_name,
                description=table.description,
                table_purpose=table.table_purpose,
                related_tables=list(table.related_tables),
            )

        print(f"📊 Tạo {len(METADATA.tables)} table nodes")
        return METADATA.tables


def create_relationships(driver):
    """Tạo edges (relationships) giữa các bảng từ FK metadata."""
    with driver.session() as session:
        for foreign_key in METADATA.foreign_keys:
            details = (
                f"{foreign_key.child_column.lower()} -> "
                f"{foreign_key.parent_column.lower()}"
            )
            session.run(
                """
                MATCH (src:Table {name: $from_name})
                MATCH (dst:Table {name: $to_name})
                MERGE (src)-[r:REFERENCES {fk_column: $fk_column, references_column: $references_column}]->(dst)
                SET r.type = $rel_type,
                    r.details = $details,
                    r.business_name = $business_name,
                    r.description = $description,
                    r.created_at = datetime()
                """,
                from_name=foreign_key.child_table,
                to_name=foreign_key.parent_table,
                fk_column=foreign_key.child_column,
                references_column=foreign_key.parent_column,
                rel_type="FK",
                details=details,
                business_name=foreign_key.business_name,
                description=foreign_key.description,
            )

        print(f"🔗 Tạo {len(METADATA.foreign_keys)} relationship edges (FK links)")


def create_named_paths(driver):
    """Tạo named paths từ relationship metadata."""
    with driver.session() as session:
        for relationship in METADATA.relationships:
            session.run(
                """
                MERGE (p:NamedPath {name: $name})
                SET p.description = $description,
                    p.domain = $domain,
                    p.tables = $tables,
                    p.join_path = $join_path,
                    p.sample_sql = $sample_sql,
                    p.created_at = datetime()
                """,
                name=relationship.name,
                description=relationship.description,
                domain=relationship.domain_name,
                tables=list(relationship.tables),
                join_path=relationship.join_path,
                sample_sql=relationship.sample_sql,
            )
            for table_name in relationship.tables:
                session.run(
                    """
                    MATCH (p:NamedPath {name: $path_name})
                    MATCH (t:Table {name: $table_name})
                    MERGE (p)-[:INCLUDES]->(t)
                    """,
                    path_name=relationship.name,
                    table_name=table_name,
                )

        print(f"📍 Tạo {len(METADATA.relationships)} named paths")


def verify_graph(driver):
    """Kiểm tra graph đã được tạo."""
    with driver.session() as session:
        table_count = session.run("MATCH (t:Table) RETURN COUNT(t) as count").single()["count"]
        rel_count = session.run(
            "MATCH ()-[r:REFERENCES]->() RETURN COUNT(r) as count"
        ).single()["count"]
        path_count = session.run(
            "MATCH (p:NamedPath) RETURN COUNT(p) as count"
        ).single()["count"]
        include_count = session.run(
            "MATCH (:NamedPath)-[r:INCLUDES]->(:Table) RETURN COUNT(r) as count"
        ).single()["count"]

        print("\n✅ KIỂM TRA GRAPH:")
        print("-" * 50)
        print(f"  Tables:        {table_count}")
        print(f"  Relationships: {rel_count}")
        print(f"  Named Paths:   {path_count}")
        print(f"  Includes:      {include_count}")


def demo_queries(driver):
    """Chạy một số demo queries."""
    with driver.session() as session:
        print("\n🔍 DEMO QUERIES:")
        print("-" * 50)

        print("\n1️⃣  Tất cả bảng trong General Ledger domain:")
        result = session.run(
            "MATCH (t:Table {domain: 'General Ledger'}) RETURN t.name as name ORDER BY t.type, t.name"
        )
        for record in result:
            print(f"   {record['name']}")

        print("\n2️⃣  Tất cả bảng trong Customer Information domain:")
        result = session.run(
            "MATCH (t:Table {domain: 'Customer Information'}) RETURN t.name as name ORDER BY t.name"
        )
        for record in result:
            print(f"   {record['name']}")

        print("\n3️⃣  Mối quan hệ từ GL_JOURNAL_LINES:")
        result = session.run(
            """
            MATCH (src:Table {name: 'GL_JOURNAL_LINES'})
                  -[r:REFERENCES]->(dst:Table)
            RETURN src.name as source, dst.name as target, r.fk_column as fk, r.details as details
            ORDER BY target
            """
        )
        for record in result:
            print(
                f"   {record['source']} -[{record['fk']}]-> {record['target']} | {record['details']}"
            )

        print("\n4️⃣  Đường dẫn từ CIF_CUSTOMERS đến GL_JOURNAL_HEADERS (cross-domain):")
        result = session.run(
            """
            MATCH path = (src:Table {name: 'CIF_CUSTOMERS'})
                         <-[:REFERENCES*..10]-(:Table)
                         -[:REFERENCES*..10]->(dst:Table {name: 'GL_JOURNAL_HEADERS'})
            RETURN [node IN nodes(path) | node.name] as path_nodes
            LIMIT 1
            """
        )
        for record in result:
            path = " → ".join(record["path_nodes"])
            print(f"   {path}")

        print("\n5️⃣  Named paths có sẵn:")
        result = session.run(
            "MATCH (p:NamedPath) RETURN p.name as name, p.domain as domain ORDER BY p.domain, p.name"
        )
        for record in result:
            print(f"   [{record['domain']}] {record['name']}")


def main():
    """Main entry point."""
    print("=" * 70)
    print("  Neo4j Relationship Graph Loader – Table JOIN Paths")
    print("=" * 70)

    driver = None
    try:
        driver = create_driver()

        print("\n1️⃣  Xóa graph cũ...")
        clear_graph(driver)

        print("\n2️⃣  Tạo table nodes...")
        create_tables(driver)

        print("\n3️⃣  Tạo FK relationships...")
        create_relationships(driver)

        print("\n4️⃣  Tạo named paths...")
        create_named_paths(driver)

        print("\n5️⃣  Kiểm tra graph...")
        verify_graph(driver)

        print("\n6️⃣  Chạy demo queries...")
        demo_queries(driver)

        print("\n✅ Hoàn thành! Neo4j relationship graph đã sẵn sàng cho SQL Writer Agent.")

    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        raise
    finally:
        if driver:
            driver.close()


if __name__ == "__main__":
    main()
