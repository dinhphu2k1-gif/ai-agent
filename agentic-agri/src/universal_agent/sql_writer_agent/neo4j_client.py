import os
import re
from typing import Iterable

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()


class Neo4jRelationshipClient:
    def __init__(self):
        self._driver = None

    @property
    def driver(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
                auth=(
                    os.environ.get("NEO4J_USER", "neo4j"),
                    os.environ.get("NEO4J_PASSWORD", "password"),
                ),
            )
        return self._driver

    def close(self):
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def extract_table_names(self, metadata_context: str) -> list[str]:
        # metadata_context = metadata_context or ""
        # table_names: list[str] = []

        # related_section_match = re.search(
        #     r"BẢNG LIÊN QUAN(?P<section>[\s\S]*?)(?:\n\s*\d+\.\s|\Z)",
        #     metadata_context,
        #     re.IGNORECASE,
        # )
        # if related_section_match:
        #     section = related_section_match.group("section")
        #     for line in section.splitlines():
        #         stripped = line.strip()
        #         if not stripped.startswith("*"):
        #             continue
        #         candidate = stripped.lstrip("*").strip()
        #         if not re.fullmatch(r"(?:GL|CIF)_[A-Z_]+", candidate):
        #             continue
        #         if candidate not in table_names:
        #             table_names.append(candidate)

        # if table_names:
        #     return table_names

        # for match in re.finditer(r"\b(?:GL|CIF)_[A-Z_]+\b", metadata_context):
        #     table_name = match.group(0)
        #     if table_name not in table_names:
        #         table_names.append(table_name)
        # return table_names
        table_names = []
        for match in re.finditer(r"\b(?:GL|CIF)_[A-Z_]+\b", metadata_context or ""):
            table_name = match.group(0)
            if table_name not in table_names:
                table_names.append(table_name)
        return table_names

    def get_direct_relationships(self, table_names: Iterable[str]) -> str:
        table_names = list(dict.fromkeys(table_names))
        if not table_names:
            return ""

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (src:Table)-[r:REFERENCES]->(dst:Table)
                WHERE src.name IN $table_names OR dst.name IN $table_names
                RETURN src.name AS source, dst.name AS target, r.fk_column AS fk_column,
                       r.references_column AS references_column, r.details AS details
                ORDER BY source, target, fk_column
                LIMIT 20
                """,
                table_names=table_names,
            )
            lines = []
            for record in result:
                lines.append(
                    f"[FK] {record['source']}.{record['fk_column']} -> "
                    f"{record['target']}.{record['references_column']}"
                )
            return "\n".join(lines)

    def find_join_paths(self, table_names: Iterable[str], max_hops: int = 4) -> str:
        table_names = list(dict.fromkeys(table_names))
        if len(table_names) < 2:
            return ""

        paths = []
        with self.driver.session() as session:
            for idx, source in enumerate(table_names):
                for target in table_names[idx + 1 :]:
                    result = session.run(
                        f"""
                        MATCH path = shortestPath((src:Table {{name: $source}})-[:REFERENCES*..{max_hops}]-(dst:Table {{name: $target}}))
                        RETURN [node IN nodes(path) | node.name] AS path_nodes
                        LIMIT 1
                        """,
                        source=source,
                        target=target,
                    )
                    record = result.single()
                    if record and record.get("path_nodes"):
                        paths.append("[PATH] " + " -> ".join(record["path_nodes"]))
        return "\n".join(dict.fromkeys(paths))

    def get_named_paths(self, table_names: Iterable[str]) -> str:
        table_names = list(dict.fromkeys(table_names))
        if not table_names:
            return ""

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (p:NamedPath)-[:INCLUDES]->(t:Table)
                WHERE t.name IN $table_names
                WITH p, collect(DISTINCT t.name) AS matched_tables
                RETURN p.name AS name, p.join_path AS join_path, p.tables AS tables, matched_tables
                ORDER BY size(matched_tables) DESC, name
                LIMIT 10
                """,
                table_names=table_names,
            )
            lines = []
            for record in result:
                lines.append(f"[NAMED_PATH] {record['name']} | {record['join_path']}")
            return "\n".join(lines)

    def collect_related_tables(
        self,
        seed_tables: Iterable[str],
        *,
        max_hops: int = 2,
        max_tables: int = 8,
    ) -> list[str]:
        """Expand seed tables via REFERENCES edges and shortestPath in Neo4j."""
        seeds = list(dict.fromkeys(t for t in seed_tables if t))
        if not seeds:
            return []

        seen = set(seeds)
        expanded = list(seeds)

        with self.driver.session() as session:
            neighbor_result = session.run(
                """
                MATCH (src:Table)-[:REFERENCES]-(dst:Table)
                WHERE src.name IN $seeds OR dst.name IN $seeds
                RETURN DISTINCT src.name AS t1, dst.name AS t2
                """,
                seeds=seeds,
            )
            for record in neighbor_result:
                for key in ("t1", "t2"):
                    name = record.get(key)
                    if name and name not in seen:
                        seen.add(name)
                        expanded.append(name)

            if len(seeds) >= 2 and max_hops >= 1:
                hop_limit = max(1, min(max_hops, 4))
                for idx, source in enumerate(seeds):
                    for target in seeds[idx + 1 :]:
                        path_result = session.run(
                            f"""
                            MATCH path = shortestPath(
                                (src:Table {{name: $source}})
                                -[:REFERENCES*..{hop_limit}]-
                                (dst:Table {{name: $target}})
                            )
                            RETURN [node IN nodes(path) | node.name] AS path_nodes
                            LIMIT 1
                            """,
                            source=source,
                            target=target,
                        )
                        record = path_result.single()
                        if not record:
                            continue
                        for name in record.get("path_nodes") or []:
                            if name and name not in seen:
                                seen.add(name)
                                expanded.append(name)

        return expanded[:max_tables]

    def format_relationships_for_metadata(
        self,
        table_names: Iterable[str],
        *,
        max_hops: int = 4,
    ) -> str:
        """Format Neo4j join info for metadata synthesizer (OpenSearch-compatible tags)."""
        names = list(dict.fromkeys(table_names))
        if not names:
            return ""

        sections: list[str] = []

        named = self.get_named_paths(names)
        if named:
            for line in named.splitlines():
                if not line.startswith("[NAMED_PATH]"):
                    continue
                body = line.replace("[NAMED_PATH] ", "", 1)
                path_name, _, join_path = body.partition(" | ")
                sections.append(
                    f"[RELATIONSHIP] {path_name}\n"
                    f"  Mô tả: Named join path from Neo4j graph\n"
                    f"  Join Path: {join_path or path_name}\n"
                    f"  Sample SQL: N/A\n"
                    f"  Bảng liên quan: {', '.join(names)}"
                )

        for line in self.find_join_paths(names, max_hops=max_hops).splitlines():
            if not line.startswith("[PATH]"):
                continue
            path_str = line.replace("[PATH] ", "", 1)
            sections.append(
                f"[RELATIONSHIP] Shortest join path\n"
                f"  Mô tả: Computed via Neo4j shortestPath\n"
                f"  Join Path: {path_str.replace(' -> ', ' → ')}\n"
                f"  Sample SQL: N/A\n"
                f"  Bảng liên quan: {path_str.replace(' -> ', ', ')}"
            )

        fk_lines = [
            line.replace("[FK] ", "", 1)
            for line in self.get_direct_relationships(names).splitlines()
            if line.startswith("[FK]")
        ]
        if fk_lines:
            sections.append(
                f"[RELATIONSHIP] Foreign key links\n"
                f"  Mô tả: Direct REFERENCES edges in Neo4j\n"
                f"  Join Path: {'; '.join(fk_lines[:15])}\n"
                f"  Sample SQL: N/A\n"
                f"  Bảng liên quan: {', '.join(names)}"
            )

        return "\n\n".join(sections)

    def build_context(self, user_input: str, metadata_context: str) -> str:
        table_names = self.extract_table_names(metadata_context)
        print("table_names: ", table_names)

        if not table_names:
            return ""

        sections = [
            self.get_named_paths(table_names),
            self.find_join_paths(table_names),
            self.get_direct_relationships(table_names),
        ]
        return "\n".join(section for section in sections if section).strip()
