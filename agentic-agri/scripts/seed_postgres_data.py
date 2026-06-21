"""
========================================================================
PostgreSQL Sample Data Loader – GL + CIF Domain Data
========================================================================
Mô tả   : Khởi tạo schema PostgreSQL và nạp dữ liệu mẫu cho GL
          (General Ledger) và CIF (Customer Information) domains.
          Dữ liệu này dùng để test SQL Writer Agent SQL execution.
Phiên bản: PostgreSQL 12+
Tác giả  : SQL Writer Agent Development
========================================================================
"""

import os
import random
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from decimal import Decimal

import psycopg2
from dotenv import load_dotenv
from psycopg2 import sql
from psycopg2.extras import execute_values

from metadata_utils import load_metadata_bundle, topological_table_order
from postgres_scenario_catalog import SCENARIOS

load_dotenv()

ROW_COUNT_PER_TABLE = 100
METADATA = load_metadata_bundle()
TABLES_BY_NAME = {table.table_name: table for table in METADATA.tables}
FKS_BY_CHILD_TABLE = defaultdict(list)
for foreign_key in METADATA.foreign_keys:
    FKS_BY_CHILD_TABLE[foreign_key.child_table].append(foreign_key)

POSTGRES_TABLE_OVERRIDES = {
    "GL_JOURNAL_LINES": {
        "checks": ["CHECK (debit_amount = 0 OR credit_amount = 0)"],
    },
    "GL_BALANCES": {
        "uniques": ["UNIQUE(account_id, period_id, cost_center_id)"],
    },
}

POSTGRES_INDEXES = [
    "CREATE INDEX idx_gl_accounts_code ON gl_accounts(account_code)",
    "CREATE INDEX idx_gl_journals_date ON gl_journal_headers(journal_date)",
    "CREATE INDEX idx_gl_journals_status ON gl_journal_headers(status)",
    "CREATE INDEX idx_cif_number ON cif_customers(cif_number)",
    "CREATE INDEX idx_balance_account_period ON gl_balances(account_id, period_id)",
]

PG_CONFIG = {
    "host": os.environ.get("PG_HOST", "localhost"),
    "port": int(os.environ.get("PG_PORT", 5432)),
    "user": os.environ.get("PG_USER", "postgres"),
    "password": os.environ.get("PG_PASSWORD", "postgres"),
    "database": os.environ.get("PG_DATABASE", "core_banking"),
}


def create_connection():
    """Tạo kết nối PostgreSQL."""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        print(
            f"✅ Kết nối PostgreSQL thành công: {PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}"
        )
        return conn
    except psycopg2.Error as e:
        print(f"⚠️  Lỗi kết nối PostgreSQL: {e}")
        raise


def parse_numeric_type(data_type: str) -> tuple[int | None, int | None]:
    match = re.search(r"NUMBER\((\d+)(?:,(\d+))?\)", data_type or "")
    if not match:
        return None, None
    precision = int(match.group(1))
    scale = int(match.group(2)) if match.group(2) else 0
    return precision, scale


def parse_char_length(data_type: str) -> int | None:
    match = re.search(r"(?:N?VARCHAR2|CHAR)\((\d+)\)", data_type or "")
    if not match:
        return None
    return int(match.group(1))


def postgres_type(column) -> str:
    data_type = (column.data_type or "").upper()
    precision, scale = parse_numeric_type(data_type)

    if data_type.startswith("NUMBER"):
        if scale and scale > 0 and precision:
            return f"NUMERIC({precision},{scale})"
        if precision is None:
            return "NUMERIC"
        if precision <= 9:
            return "INTEGER"
        if precision <= 18:
            return "BIGINT"
        return f"NUMERIC({precision},0)"
    if data_type.startswith("VARCHAR2") or data_type.startswith("NVARCHAR2"):
        length = parse_char_length(data_type) or 255
        return f"VARCHAR({length})"
    if data_type.startswith("CHAR"):
        length = parse_char_length(data_type) or 1
        return f"CHAR({length})"
    if data_type.startswith("DATE"):
        return "DATE"
    if data_type.startswith("TIMESTAMP"):
        return "TIMESTAMP"
    return "TEXT"


def is_nullable(column) -> bool:
    if column.is_primary_key:
        return False
    upper_name = column.column_name.upper()
    if upper_name in {
        "STATUS",
        "CREATED_AT",
        "UPDATED_AT",
        "LAST_UPDATED",
        "PERIOD_ID",
        "JOURNAL_ID",
        "ACCOUNT_ID",
    }:
        return False
    return True


def quoted_identifier(name: str) -> sql.Identifier:
    return sql.Identifier(name.lower())


def build_column_definition(column) -> sql.Composed:
    parts = [
        quoted_identifier(column.column_name),
        sql.SQL(postgres_type(column)),
    ]
    if column.is_primary_key:
        parts.append(sql.SQL("PRIMARY KEY"))
    if not is_nullable(column):
        parts.append(sql.SQL("NOT NULL"))
    return sql.SQL(" ").join(parts)


def build_foreign_key_definition(foreign_key) -> sql.Composed:
    constraint_name = (
        f"fk_{foreign_key.child_table.lower()}_{foreign_key.child_column.lower()}"
    )
    return sql.SQL(
        "CONSTRAINT {} FOREIGN KEY ({}) REFERENCES {} ({})"
    ).format(
        sql.Identifier(constraint_name),
        quoted_identifier(foreign_key.child_column),
        sql.Identifier(foreign_key.parent_table.lower()),
        quoted_identifier(foreign_key.parent_column),
    )


def build_extra_constraints(table_name: str) -> list[sql.SQL]:
    extras = []
    overrides = POSTGRES_TABLE_OVERRIDES.get(table_name, {})
    for constraint in overrides.get("checks", []):
        extras.append(sql.SQL(constraint))
    for constraint in overrides.get("uniques", []):
        extras.append(sql.SQL(constraint))
    return extras


def drop_schema(conn):
    cursor = conn.cursor()
    drop_order = list(reversed(topological_table_order(METADATA.tables, METADATA.foreign_keys)))
    for table_name in drop_order:
        cursor.execute(
            sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(
                sql.Identifier(table_name.lower())
            )
        )
    conn.commit()
    print("🗑️  Xóa bảng cũ (nếu có)...")


def create_schema(conn):
    """Tạo schema PostgreSQL từ metadata."""
    cursor = conn.cursor()
    drop_schema(conn)

    create_order = topological_table_order(METADATA.tables, METADATA.foreign_keys)
    for table_name in create_order:
        table = TABLES_BY_NAME[table_name]
        definitions = [build_column_definition(column) for column in table.columns]
        definitions.extend(
            build_foreign_key_definition(foreign_key)
            for foreign_key in FKS_BY_CHILD_TABLE.get(table_name, [])
        )
        definitions.extend(build_extra_constraints(table_name))

        statement = sql.SQL("CREATE TABLE {} ({})").format(
            sql.Identifier(table.pg_name),
            sql.SQL(",\n    ").join(definitions),
        )
        cursor.execute(statement)
        print(f"📋 Tạo bảng {table.pg_name}")

    for index_statement in POSTGRES_INDEXES:
        cursor.execute(index_statement)
    print("📍 Tạo indexes")
    conn.commit()


class GenerationContext:
    def __init__(self):
        self.random = random.Random(42)
        self.generated_rows: dict[str, list[dict]] = {}
        self.rows_by_pk: dict[str, dict[object, dict]] = {}
        self.pk_columns = {
            table.table_name: next(
                (column.pg_name for column in table.columns if column.is_primary_key),
                None,
            )
            for table in METADATA.tables
        }
        self.customer_ids_by_index: list[int] = []
        self.account_ids_by_index: list[int] = []
        self.cost_center_ids_by_index: list[int] = []
        self.period_ids_by_index: list[int] = []
        self.journal_line_targets: dict[int, list[dict]] = defaultdict(list)

    def register_rows(self, table_name: str, rows: list[dict]):
        self.generated_rows[table_name] = rows
        pk_column = self.pk_columns.get(table_name)
        if pk_column:
            self.rows_by_pk[table_name] = {row[pk_column]: row for row in rows}
        if table_name == "CIF_CUSTOMERS":
            self.customer_ids_by_index = [row[pk_column] for row in rows]
        elif table_name == "GL_ACCOUNTS":
            self.account_ids_by_index = [row[pk_column] for row in rows]
        elif table_name == "GL_COST_CENTERS":
            self.cost_center_ids_by_index = [row[pk_column] for row in rows]
        elif table_name == "GL_PERIODS":
            self.period_ids_by_index = [row[pk_column] for row in rows]

    def parent_values(self, table_name: str, column_name: str) -> list[object]:
        return [row[column_name.lower()] for row in self.generated_rows.get(table_name, [])]


CTX = GenerationContext()


def decimal_amount(base: int, scale: int = 2) -> Decimal:
    return Decimal(base).quantize(Decimal("1." + ("0" * scale)))


def nth_period(index: int) -> tuple[str, int, int, date, date, str, date | None]:
    year = 2020 + ((index - 1) // 12)
    month = ((index - 1) % 12) + 1
    start = date(year, month, 1)
    if month == 12:
        end = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end = date(year, month + 1, 1) - timedelta(days=1)
    status = "CLOSED" if index <= 80 else "OPEN"
    closing_date = end + timedelta(days=2) if status == "CLOSED" else None
    return f"{year}-{month:02d}", year, month, start, end, status, closing_date


def build_period_rows(table) -> list[dict]:
    rows = []
    for index in range(1, ROW_COUNT_PER_TABLE + 1):
        period_name, year, number, start, end, status, closing_date = nth_period(index)
        rows.append(
            {
                "period_id": index,
                "period_name": period_name,
                "fiscal_year": year,
                "period_number": number,
                "start_date": start,
                "end_date": end,
                "status": status,
                "closing_date": closing_date,
            }
        )
    return rows


def build_cost_center_rows(table) -> list[dict]:
    rows = []
    prefixes = ["HO", "NORTH", "SOUTH", "CENTRAL", "OPS"]
    types = ["HEAD_OFFICE", "BRANCH", "SUB_BRANCH", "SUPPORT"]
    for index in range(1, ROW_COUNT_PER_TABLE + 1):
        region = prefixes[(index - 1) % len(prefixes)]
        rows.append(
            {
                "cost_center_id": index,
                "cost_center_code": f"{region[:2]}-{index:03d}",
                "cost_center_name": f"{region.title()} Cost Center {index:03d}",
                "cost_center_type": types[(index - 1) % len(types)],
                "region_code": region,
                "manager_emp_id": 10000 + index,
                "status": "ACTIVE" if index % 10 else "INACTIVE",
            }
        )
    return rows


def build_account_rows(table) -> list[dict]:
    account_types = ["ASSET", "LIABILITY", "EQUITY", "REVENUE", "EXPENSE"]
    currency_codes = ["VND", "USD", "EUR"]
    rows = []
    for index in range(1, ROW_COUNT_PER_TABLE + 1):
        account_type = account_types[(index - 1) % len(account_types)]
        rows.append(
            {
                "account_id": index,
                "account_code": f"{1000 + index:04d}",
                "account_name": f"{account_type.title()} Account {index:03d}",
                "account_type": account_type,
                "account_level": 4 if index > 10 else 3,
                "parent_account_id": None if index <= 10 else ((index - 1) % 10) + 1,
                "currency_code": currency_codes[(index - 1) % len(currency_codes)],
                "is_control_account": "Y" if index <= 10 else "N",
                "status": "ACTIVE" if index % 15 else "INACTIVE",
                "effective_date": date(2020, 1, 1) + timedelta(days=index),
                "end_date": None if index % 15 else date(2030, 12, 31),
                "created_at": datetime(2024, 1, 1, 8, 0, 0) + timedelta(days=index),
            }
        )
    return rows


def build_customer_rows(table) -> list[dict]:
    rows = []
    segments = ["MASS", "PREMIUM", "VIP", "PRIVATE", "SME", "CORPORATE"]
    risk_ratings = ["LOW", "MEDIUM", "HIGH", "PROHIBITED"]
    for index in range(1, ROW_COUNT_PER_TABLE + 1):
        customer_type = "CORPORATE" if index % 10 == 0 else "INDIVIDUAL"
        full_name = (
            f"CÔNG TY MẪU {index:03d}"
            if customer_type == "CORPORATE"
            else f"KHÁCH HÀNG {index:03d}"
        )
        rows.append(
            {
                "customer_id": index,
                "cif_number": f"CIF{index:010d}",
                "customer_type": customer_type,
                "full_name": full_name,
                "date_of_birth": None if customer_type == "CORPORATE" else date(1980, 1, 1) + timedelta(days=index * 73),
                "gender": "O" if customer_type == "CORPORATE" else ("M" if index % 2 else "F"),
                "phone_number": f"+8490{index:07d}",
                "email": f"customer{index:03d}@example.com",
                "customer_segment": segments[(index - 1) % len(segments)],
                "risk_rating": risk_ratings[(index - 1) % len(risk_ratings)],
                "onboarding_date": date(2020, 1, 1) + timedelta(days=index * 11),
                "status": "ACTIVE" if index % 12 else "DORMANT",
            }
        )
    return rows


def build_identification_rows(table) -> list[dict]:
    rows = []
    id_types = ["CMND", "CCCD", "PASSPORT", "GPKD", "DKKD", "MILITARY_ID"]
    for index in range(1, ROW_COUNT_PER_TABLE + 1):
        customer_id = CTX.customer_ids_by_index[index - 1]
        issued = date(2015, 1, 1) + timedelta(days=index * 19)
        rows.append(
            {
                "identification_id": index,
                "customer_id": customer_id,
                "id_type": id_types[(index - 1) % len(id_types)],
                "id_number": f"ID{index:010d}",
                "issue_date": issued,
                "expiry_date": issued + timedelta(days=3650),
                "issue_place": f"Authority {((index - 1) % 20) + 1}",
                "is_primary": "Y" if index % 2 else "N",
            }
        )
    return rows


def build_address_rows(table) -> list[dict]:
    rows = []
    address_types = ["HOME", "TEMPORARY", "OFFICE", "REGISTERED", "MAILING"]
    provinces = ["HN", "HCM", "DN", "HP", "CT"]
    for index in range(1, ROW_COUNT_PER_TABLE + 1):
        customer_id = CTX.customer_ids_by_index[index - 1]
        rows.append(
            {
                "address_id": index,
                "customer_id": customer_id,
                "address_type": address_types[(index - 1) % len(address_types)],
                "address_line": f"{index} Sample Street",
                "ward_name": f"Ward {((index - 1) % 25) + 1}",
                "district_name": f"District {((index - 1) % 20) + 1}",
                "province_code": provinces[(index - 1) % len(provinces)],
                "is_default": "Y" if index % 3 == 1 else "N",
            }
        )
    return rows


def build_cif_account_rows(table) -> list[dict]:
    rows = []
    roles = ["OWNER", "CO_OWNER", "AUTHORIZED", "BENEFICIARY", "GUARDIAN"]
    statuses = ["ACTIVE", "FROZEN", "DORMANT", "CLOSED"]
    for index in range(1, ROW_COUNT_PER_TABLE + 1):
        rows.append(
            {
                "cif_account_id": index,
                "customer_id": CTX.customer_ids_by_index[index - 1],
                "account_id": CTX.account_ids_by_index[(index - 1) % len(CTX.account_ids_by_index)],
                "account_number": f"AC{index:016d}"[:20],
                "account_role": roles[(index - 1) % len(roles)],
                "opening_date": date(2021, 1, 1) + timedelta(days=index * 5),
                "closing_date": None if index % 20 else date(2025, 12, 31),
                "status": statuses[(index - 1) % len(statuses)],
            }
        )
    return rows


def build_journal_header_rows(table) -> list[dict]:
    rows = []
    types = ["MANUAL", "AUTO_ACCRUAL", "AUTO_REVERSAL"]
    statuses = ["DRAFT", "PENDING_APPROVAL", "APPROVED", "POSTED"]
    source_systems = ["GL_MANUAL", "LOAN_SYSTEM", "DEPOSIT_SYSTEM"]
    for index in range(1, ROW_COUNT_PER_TABLE + 1):
        period_id = CTX.period_ids_by_index[(index - 1) % len(CTX.period_ids_by_index)]
        journal_date = date(2024, 1, 1) + timedelta(days=index)
        status = statuses[(index - 1) % len(statuses)]
        rows.append(
            {
                "journal_id": index,
                "journal_number": f"JV-{index:08d}"[:30],
                "journal_date": journal_date,
                "accounting_date": journal_date,
                "period_id": period_id,
                "journal_type": types[(index - 1) % len(types)],
                "description": f"Generated journal entry {index:03d}",
                "reference_number": f"REF-{index:06d}",
                "source_system": source_systems[(index - 1) % len(source_systems)],
                "status": status,
                "total_debit": decimal_amount(index * 1000),
                "total_credit": decimal_amount(index * 1000),
                "reversal_flag": "Y" if index % 20 == 0 else "N",
                "reversal_date": journal_date + timedelta(days=1) if index % 20 == 0 else None,
                "created_by": f"system_{((index - 1) % 5) + 1}",
                "approved_by": None if status in {"DRAFT", "PENDING_APPROVAL"} else f"approver_{((index - 1) % 3) + 1}",
            }
        )
    return rows


def build_journal_line_rows(table) -> list[dict]:
    rows = []
    tax_codes = ["VAT10", "VAT8", "VAT0"]
    reconciliation_statuses = ["UNRECONCILED", "RECONCILED", "PARTIALLY_RECONCILED"]
    for index in range(1, ROW_COUNT_PER_TABLE + 1):
        journal_id = ((index - 1) % ROW_COUNT_PER_TABLE) + 1
        amount = decimal_amount(5000 + index * 25)
        debit_amount = amount if index % 2 else decimal_amount(0)
        credit_amount = decimal_amount(0) if index % 2 else amount
        rows.append(
            {
                "line_id": index,
                "journal_id": journal_id,
                "line_number": (index - 1) // 2 + 1 if index % 2 else index // 2,
                "account_id": CTX.account_ids_by_index[(index - 1) % len(CTX.account_ids_by_index)],
                "cost_center_id": CTX.cost_center_ids_by_index[(index - 1) % len(CTX.cost_center_ids_by_index)],
                "debit_amount": debit_amount,
                "credit_amount": credit_amount,
                "currency_code": "VND" if index % 5 else "USD",
                "amount_original": amount,
                "exchange_rate": Decimal("1.000000") if index % 5 else Decimal("24.500000"),
                "line_description": f"Generated journal line {index:03d}",
                "tax_code": tax_codes[(index - 1) % len(tax_codes)],
                "reconciliation_status": reconciliation_statuses[(index - 1) % len(reconciliation_statuses)],
                "customer_id": CTX.customer_ids_by_index[(index - 1) % len(CTX.customer_ids_by_index)] if index % 3 else None,
            }
        )
    return rows


def build_balance_rows(table) -> list[dict]:
    rows = []
    for index in range(1, ROW_COUNT_PER_TABLE + 1):
        opening = decimal_amount(index * 2000)
        activity_dr = decimal_amount(index * 125)
        activity_cr = decimal_amount(index * 40)
        rows.append(
            {
                "balance_id": index,
                "account_id": CTX.account_ids_by_index[index - 1],
                "cost_center_id": CTX.cost_center_ids_by_index[index - 1],
                "period_id": CTX.period_ids_by_index[index - 1],
                "currency_code": "VND" if index % 5 else "USD",
                "opening_balance_dr": opening,
                "opening_balance_cr": decimal_amount(0),
                "period_activity_dr": activity_dr,
                "period_activity_cr": activity_cr,
                "closing_balance_dr": opening + activity_dr,
                "closing_balance_cr": activity_cr,
                "ytd_activity_dr": opening + activity_dr,
                "ytd_activity_cr": activity_cr,
                "last_updated": datetime(2024, 5, 1, 8, 0, 0) + timedelta(days=index),
            }
        )
    return rows


def generic_value(column, row_index: int):
    upper_name = column.column_name.upper()
    data_type = column.data_type.upper()
    allowed = list(column.allowed_values)

    if column.is_primary_key:
        return row_index
    if column.is_foreign_key:
        for foreign_key in FKS_BY_CHILD_TABLE[column.table_name]:
            if foreign_key.child_column == column.column_name:
                parent_values = CTX.parent_values(
                    foreign_key.parent_table,
                    foreign_key.parent_column,
                )
                if upper_name == "CUSTOMER_ID" and column.table_name == "GL_JOURNAL_LINES" and row_index % 3 == 0:
                    return None
                return parent_values[(row_index - 1) % len(parent_values)]
    if upper_name.endswith("_NUMBER"):
        if upper_name == "CIF_NUMBER":
            return f"CIF{row_index:010d}"
        prefix = upper_name.replace("_NUMBER", "")[:4]
        return f"{prefix}-{row_index:06d}"
    if upper_name.endswith("_CODE"):
        prefix = upper_name.replace("_CODE", "")[:4]
        return f"{prefix}{row_index:04d}"
    if upper_name == "STATUS":
        return allowed[(row_index - 1) % len(allowed)] if allowed else "ACTIVE"
    if upper_name in {"IS_CONTROL_ACCOUNT", "REVERSAL_FLAG", "IS_PRIMARY", "IS_DEFAULT"}:
        return "Y" if row_index % 2 else "N"
    if upper_name == "GENDER":
        return ["M", "F", "O"][(row_index - 1) % 3]
    if upper_name == "COUNTRY_CODE":
        return "VN"
    if upper_name == "CURRENCY_CODE":
        return ["VND", "USD", "EUR"][(row_index - 1) % 3]
    if "EMAIL" in upper_name:
        return f"row{row_index:03d}@example.com"
    if "PHONE" in upper_name:
        return f"+849{row_index:08d}"[:12]
    if data_type.startswith("DATE"):
        return date(2024, 1, 1) + timedelta(days=row_index)
    if data_type.startswith("TIMESTAMP"):
        return datetime(2024, 1, 1, 8, 0, 0) + timedelta(days=row_index)
    if data_type.startswith("NUMBER"):
        precision, scale = parse_numeric_type(data_type)
        if scale and scale > 0:
            return decimal_amount(row_index * 100, scale)
        return row_index
    if data_type.startswith("VARCHAR2") or data_type.startswith("NVARCHAR2"):
        length = parse_char_length(data_type) or 50
        value = f"{column.table_name.title()} {column.column_name.title()} {row_index}"
        return value[:length]
    return None if is_nullable(column) else f"{column.column_name}_{row_index}"


TABLE_ROW_BUILDERS = {
    "GL_PERIODS": build_period_rows,
    "GL_COST_CENTERS": build_cost_center_rows,
    "GL_ACCOUNTS": build_account_rows,
    "CIF_CUSTOMERS": build_customer_rows,
    "CIF_IDENTIFICATIONS": build_identification_rows,
    "CIF_ADDRESSES": build_address_rows,
    "CIF_ACCOUNTS": build_cif_account_rows,
    "GL_JOURNAL_HEADERS": build_journal_header_rows,
    "GL_JOURNAL_LINES": build_journal_line_rows,
    "GL_BALANCES": build_balance_rows,
}


def build_rows_for_table(table) -> list[dict]:
    builder = TABLE_ROW_BUILDERS.get(table.table_name)
    if builder:
        rows = builder(table)
    else:
        rows = []
        for row_index in range(1, ROW_COUNT_PER_TABLE + 1):
            row = {}
            for column in table.columns:
                row[column.pg_name] = generic_value(column, row_index)
            rows.append(row)

    normalized_rows = []
    for row in rows:
        normalized = {}
        for column in table.columns:
            normalized[column.pg_name] = row.get(column.pg_name)
        normalized_rows.append(normalized)
    return normalized_rows


def insert_rows(conn, table, rows: list[dict]):
    cursor = conn.cursor()
    columns = [column.pg_name for column in table.columns]
    insert_statement = sql.SQL("INSERT INTO {} ({}) VALUES %s").format(
        sql.Identifier(table.pg_name),
        sql.SQL(", ").join(sql.Identifier(column) for column in columns),
    )
    values = [tuple(row[column] for column in columns) for row in rows]
    execute_values(cursor, insert_statement.as_string(conn), values)
    conn.commit()
    print(f"📥 Nạp {table.table_name} ({len(rows)} dòng)")


def insert_sample_data(conn):
    """Nạp dữ liệu mẫu vào database từ metadata."""
    for table_name in topological_table_order(METADATA.tables, METADATA.foreign_keys):
        table = TABLES_BY_NAME[table_name]
        rows = build_rows_for_table(table)
        insert_rows(conn, table, rows)
        CTX.register_rows(table_name, rows)


def insert_scenario_anchor_data(conn):
    """Bổ sung dữ liệu có chủ đích để 10 scenario business luôn query ra rows."""
    cursor = conn.cursor()

    scenario_specs = {
        "SCN01": {"customer_id": 1, "account_id": 1, "period_id": 100, "cost_center_id": 1, "customer_status": "ACTIVE", "account_status": "ACTIVE", "customer_segment": "MASS", "currency_code": "VND", "corporate": False},
        "SCN02": {"customer_id": 2, "account_id": 2, "period_id": 99, "cost_center_id": 2, "customer_status": "ACTIVE", "account_status": "ACTIVE", "customer_segment": "PREMIUM", "currency_code": "VND", "corporate": False},
        "SCN03": {"customer_id": 3, "account_id": 3, "period_id": 98, "cost_center_id": 3, "customer_status": "ACTIVE", "account_status": "ACTIVE", "customer_segment": "VIP", "currency_code": "VND", "corporate": False},
        "SCN04": {"customer_id": 4, "account_id": 4, "period_id": 97, "cost_center_id": 4, "customer_status": "ACTIVE", "account_status": "ACTIVE", "customer_segment": "SME", "currency_code": "USD", "corporate": False},
        "SCN05": {"customer_id": 5, "account_id": 5, "period_id": 96, "cost_center_id": 5, "customer_status": "ACTIVE", "account_status": "ACTIVE", "customer_segment": "MASS", "currency_code": "VND", "corporate": False},
        "SCN06": {"customer_id": 10, "account_id": 10, "period_id": 95, "cost_center_id": 6, "customer_status": "ACTIVE", "account_status": "ACTIVE", "customer_segment": "CORPORATE", "currency_code": "USD", "corporate": True},
        "SCN07": {"customer_id": 7, "account_id": 7, "period_id": 94, "cost_center_id": 7, "customer_status": "ACTIVE", "account_status": "ACTIVE", "customer_segment": "VIP", "currency_code": "VND", "corporate": False},
        "SCN08": {"customer_id": 8, "account_id": 8, "period_id": 93, "cost_center_id": 8, "customer_status": "ACTIVE", "account_status": "ACTIVE", "customer_segment": "PREMIUM", "currency_code": "EUR", "corporate": False},
        "SCN09": {"customer_id": 9, "account_id": 9, "period_id": 92, "cost_center_id": 9, "customer_status": "ACTIVE", "account_status": "ACTIVE", "customer_segment": "PRIVATE", "currency_code": "USD", "corporate": False},
        "SCN10": {"customer_id": 11, "account_id": 11, "period_id": 91, "cost_center_id": 10, "customer_status": "ACTIVE", "account_status": "FROZEN", "customer_segment": "MASS", "currency_code": "VND", "corporate": False},
    }

    for scenario_id, spec in scenario_specs.items():
        customer_type = "CORPORATE" if spec["corporate"] else "INDIVIDUAL"
        full_name = f"CÔNG TY ANCHOR {scenario_id}" if spec["corporate"] else f"KHÁCH HÀNG ANCHOR {scenario_id}"
        gender = "O" if spec["corporate"] else ("M" if spec["customer_id"] % 2 else "F")
        cursor.execute(
            """
            UPDATE cif_customers
            SET full_name = %s,
                customer_type = %s,
                customer_segment = %s,
                status = %s,
                gender = %s,
                onboarding_date = %s,
                risk_rating = %s
            WHERE customer_id = %s
            """,
            (
                full_name,
                customer_type,
                spec["customer_segment"],
                spec["customer_status"],
                gender,
                date(2024, 1, 1) + timedelta(days=spec["customer_id"]),
                "LOW" if scenario_id != "SCN10" else "HIGH",
                spec["customer_id"],
            ),
        )

        account_type = "ASSET" if scenario_id not in {"SCN04", "SCN09"} else "LIABILITY"
        cursor.execute(
            """
            UPDATE gl_accounts
            SET account_name = %s,
                account_type = %s,
                currency_code = %s,
                status = %s,
                is_control_account = 'N',
                parent_account_id = NULL
            WHERE account_id = %s
            """,
            (
                f"Scenario Account {scenario_id}",
                account_type,
                spec["currency_code"],
                "ACTIVE",
                spec["account_id"],
            ),
        )

        cursor.execute(
            """
            UPDATE gl_cost_centers
            SET cost_center_name = %s,
                region_code = %s,
                status = 'ACTIVE'
            WHERE cost_center_id = %s
            """,
            (
                f"Scenario Cost Center {scenario_id}",
                f"R{spec['cost_center_id']:02d}",
                spec["cost_center_id"],
            ),
        )

        cursor.execute(
            """
            UPDATE gl_periods
            SET period_name = %s,
                fiscal_year = 2026,
                period_number = %s,
                status = 'OPEN'
            WHERE period_id = %s
            """,
            (
                f"2026-{spec['period_id'] - 90:02d}",
                spec["period_id"] - 90,
                spec["period_id"],
            ),
        )

        cursor.execute(
            """
            UPDATE cif_identifications
            SET id_number = %s,
                is_primary = 'Y'
            WHERE customer_id = %s
            """,
            (
                f"{scenario_id}-ID",
                spec["customer_id"],
            ),
        )

        cursor.execute(
            """
            UPDATE cif_addresses
            SET address_line = %s,
                is_default = 'Y',
                province_code = %s
            WHERE customer_id = %s
            """,
            (
                f"{scenario_id} Anchor Address",
                "HN" if spec["customer_id"] % 2 else "HCM",
                spec["customer_id"],
            ),
        )

        cursor.execute(
            """
            UPDATE cif_accounts
            SET account_id = %s,
                account_number = %s,
                account_role = 'OWNER',
                status = %s,
                opening_date = %s,
                closing_date = CASE WHEN %s = 'ACTIVE' THEN NULL ELSE DATE '2025-12-31' END
            WHERE customer_id = %s
            """,
            (
                spec["account_id"],
                f"{scenario_id}-ACC",
                spec["account_status"],
                date(2024, 1, 1) + timedelta(days=spec["customer_id"]),
                spec["account_status"],
                spec["customer_id"],
            ),
        )

        cursor.execute(
            """
            UPDATE gl_journal_headers
            SET period_id = %s,
                journal_date = %s,
                accounting_date = %s,
                description = %s,
                status = 'APPROVED',
                source_system = 'GL_MANUAL',
                total_debit = %s,
                total_credit = %s,
                reference_number = %s,
                reversal_flag = 'N',
                reversal_date = NULL,
                approved_by = 'scenario_approver'
            WHERE journal_id = %s
            """,
            (
                spec["period_id"],
                date(2026, max(spec["period_id"] - 90, 1), 15),
                date(2026, max(spec["period_id"] - 90, 1), 15),
                f"Scenario Journal {scenario_id}",
                decimal_amount(spec["account_id"] * 1000),
                decimal_amount(spec["account_id"] * 1000),
                f"{scenario_id}-REF",
                spec["account_id"],
            ),
        )

        cursor.execute(
            """
            UPDATE gl_journal_lines
            SET journal_id = %s,
                account_id = %s,
                cost_center_id = %s,
                customer_id = %s,
                debit_amount = %s,
                credit_amount = 0,
                currency_code = %s,
                amount_original = %s,
                exchange_rate = %s,
                line_description = %s,
                tax_code = 'VAT10',
                reconciliation_status = 'RECONCILED'
            WHERE line_id = %s
            """,
            (
                spec["account_id"],
                spec["account_id"],
                spec["cost_center_id"],
                spec["customer_id"],
                decimal_amount(spec["account_id"] * 1000),
                spec["currency_code"],
                decimal_amount(spec["account_id"] * 1000, 4),
                Decimal("1.000000") if spec["currency_code"] == "VND" else Decimal("24.500000"),
                f"Scenario Line {scenario_id}",
                spec["account_id"],
            ),
        )

        cursor.execute(
            """
            UPDATE gl_balances
            SET account_id = %s,
                cost_center_id = %s,
                period_id = %s,
                currency_code = %s,
                opening_balance_dr = %s,
                opening_balance_cr = 0,
                period_activity_dr = %s,
                period_activity_cr = 0,
                closing_balance_dr = %s,
                closing_balance_cr = 0,
                ytd_activity_dr = %s,
                ytd_activity_cr = 0,
                last_updated = %s
            WHERE balance_id = %s
            """,
            (
                spec["account_id"],
                spec["cost_center_id"],
                spec["period_id"],
                spec["currency_code"],
                decimal_amount(spec["account_id"] * 500),
                decimal_amount(spec["account_id"] * 250),
                decimal_amount(spec["account_id"] * 750),
                decimal_amount(spec["account_id"] * 750),
                datetime(2026, max(spec["period_id"] - 90, 1), 20, 8, 0, 0),
                spec["account_id"],
            ),
        )

    conn.commit()
    print(f"🎯 Đã nạp scenario anchor data cho {len(scenario_specs)} kịch bản")


def verify_scenarios(conn):
    """Kiểm tra mọi canonical SQL của scenario đều trả dữ liệu."""
    cursor = conn.cursor()
    print("\n🧪 KIỂM TRA 10 KỊCH BẢN:")
    print("-" * 80)
    for scenario in SCENARIOS:
        for question in scenario.questions:
            cursor.execute(question.canonical_sql)
            rows = cursor.fetchall()
            row_count = len(rows)
            print(f"  {scenario.scenario_id} | {question.question_id} | rows={row_count:3d} | {question.question}")
            if row_count < question.min_expected_rows:
                raise AssertionError(
                    f"Scenario {scenario.scenario_id} question {question.question_id} returned {row_count} rows"
                )


def verify_data(conn):
    """Kiểm tra dữ liệu đã được nạp."""
    cursor = conn.cursor()

    print("\n✅ KIỂM TRA DỮ LIỆU:")
    print("-" * 50)
    total = 0
    for table in METADATA.tables:
        cursor.execute(
            sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table.pg_name))
        )
        count = cursor.fetchone()[0]
        print(f"  {table.table_name:20s}: {count:5d} dòng")
        total += count
    print("-" * 50)
    print(f"  {'TỔNG CỘNG':20s}: {total:5d} dòng")

    print("\n🔗 KIỂM TRA FK ORPHAN:")
    print("-" * 50)
    for foreign_key in METADATA.foreign_keys:
        query = sql.SQL(
            """
            SELECT COUNT(*)
            FROM {child} c
            LEFT JOIN {parent} p
              ON c.{child_column} = p.{parent_column}
            WHERE c.{child_column} IS NOT NULL
              AND p.{parent_column} IS NULL
            """
        ).format(
            child=sql.Identifier(foreign_key.child_pg_table),
            parent=sql.Identifier(foreign_key.parent_pg_table),
            child_column=sql.Identifier(foreign_key.child_pg_column),
            parent_column=sql.Identifier(foreign_key.parent_pg_column),
        )
        cursor.execute(query)
        orphan_count = cursor.fetchone()[0]
        print(
            f"  {foreign_key.child_table}.{foreign_key.child_column:20s} -> "
            f"{foreign_key.parent_table}.{foreign_key.parent_column:20s}: {orphan_count}"
        )

    verify_scenarios(conn)


def demo_queries(conn):
    """Chạy một số query demo."""
    cursor = conn.cursor()

    print("\n🔍 DEMO QUERIES:")
    print("-" * 50)

    print("\n1️⃣  Danh sách tài khoản theo loại:")
    cursor.execute(
        """
        SELECT account_code, account_name, account_type, status
        FROM gl_accounts
        ORDER BY account_type, account_code
        LIMIT 10
        """
    )
    for row in cursor.fetchall():
        print(f"   {row[0]:10s} | {row[1]:30s} | {row[2]:10s} | {row[3]}")

    print("\n2️⃣  Liên kết khách hàng - tài khoản GL:")
    cursor.execute(
        """
        SELECT c.cif_number, c.full_name, ca.account_number, a.account_code, a.account_name
        FROM cif_customers c
        JOIN cif_accounts ca ON c.customer_id = ca.customer_id
        JOIN gl_accounts a ON ca.account_id = a.account_id
        LIMIT 10
        """
    )
    for row in cursor.fetchall():
        print(
            f"   {row[0]} | {row[1]:20s} | {row[2]:10s} | {row[3]:10s} | {row[4]}"
        )

    print("\n3️⃣  Bút toán kế toán được phê duyệt:")
    cursor.execute(
        """
        SELECT j.journal_number, j.journal_date, j.description, j.total_debit, j.total_credit, COUNT(l.line_id) as lines
        FROM gl_journal_headers j
        LEFT JOIN gl_journal_lines l ON j.journal_id = l.journal_id
        WHERE j.status IN ('APPROVED', 'POSTED')
        GROUP BY j.journal_id, j.journal_number, j.journal_date, j.description, j.total_debit, j.total_credit
        LIMIT 10
        """
    )
    for row in cursor.fetchall():
        print(
            f"   {row[0]:15s} | {row[1]} | {row[2]:30s} | {row[3]:12.2f} | {row[4]:12.2f} | {row[5]} lines"
        )

    print("\n4️⃣  Số dư tài khoản theo kỳ:")
    cursor.execute(
        """
        SELECT a.account_code, a.account_name, p.period_name,
               b.opening_balance_dr - b.opening_balance_cr as opening,
               b.period_activity_dr - b.period_activity_cr as activity,
               b.closing_balance_dr - b.closing_balance_cr as closing
        FROM gl_balances b
        JOIN gl_accounts a ON b.account_id = a.account_id
        JOIN gl_periods p ON b.period_id = p.period_id
        LIMIT 10
        """
    )
    for row in cursor.fetchall():
        print(
            f"   {row[0]:10s} | {row[1]:25s} | {row[2]} | {row[3]:12.2f} | {row[4]:12.2f} | {row[5]:12.2f}"
        )


def main():
    """Main entry point."""
    print("=" * 70)
    print("  PostgreSQL Sample Data Loader – GL + CIF Domains")
    print("=" * 70)

    try:
        conn = create_connection()

        print("\n1️⃣  Tạo schema...")
        create_schema(conn)

        print("\n2️⃣  Nạp dữ liệu mẫu...")
        insert_sample_data(conn)
        insert_scenario_anchor_data(conn)

        print("\n3️⃣  Kiểm tra dữ liệu...")
        verify_data(conn)

        print("\n4️⃣  Chạy demo queries...")
        demo_queries(conn)

        conn.close()
        print("\n✅ Hoàn thành! PostgreSQL sample data đã sẵn sàng cho SQL Writer Agent.")

    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        raise


if __name__ == "__main__":
    main()
