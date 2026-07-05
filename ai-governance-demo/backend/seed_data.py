#!/usr/bin/env python3
"""Seed all demo data: banking tables, resource catalog, users, roles, permissions.

Usage:
    python seed_data.py

Idempotent — safe to run multiple times.
"""
from __future__ import annotations

import uuid
import sys
from pathlib import Path

# Ensure backend/ is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import text, select
from database import engine, SessionLocal, Base
from models.resource import Resource, Database, Schema, Table, ColumnResource
from models.identity import User, Role, UserRole
from models.permission import Permission, RowFilter, ColumnMask


# ─── Deterministic UUIDs ──────────────────────────────────

NS = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def _id(label: str) -> uuid.UUID:
    return uuid.uuid5(NS, label)


# ─── 1. Physical Banking Tables ──────────────────────────

BANKING_DDL = """
CREATE SCHEMA IF NOT EXISTS core_banking;

DROP TABLE IF EXISTS core_banking.deposits CASCADE;
DROP TABLE IF EXISTS core_banking.loans CASCADE;
DROP TABLE IF EXISTS core_banking.transactions CASCADE;
DROP TABLE IF EXISTS core_banking.customers CASCADE;

CREATE TABLE core_banking.customers (
    customer_id   SERIAL PRIMARY KEY,
    full_name     VARCHAR(255) NOT NULL,
    phone_number  VARCHAR(20),
    id_number     VARCHAR(20),
    branch_code   VARCHAR(10) NOT NULL,
    balance       NUMERIC(15,2) DEFAULT 0
);

CREATE TABLE core_banking.transactions (
    txn_id        SERIAL PRIMARY KEY,
    customer_id   INT REFERENCES core_banking.customers(customer_id),
    amount        NUMERIC(15,2) NOT NULL,
    txn_type      VARCHAR(20),
    txn_date      DATE NOT NULL,
    branch_code   VARCHAR(10) NOT NULL
);

CREATE TABLE core_banking.loans (
    loan_id       SERIAL PRIMARY KEY,
    customer_id   INT REFERENCES core_banking.customers(customer_id),
    loan_amount   NUMERIC(15,2) NOT NULL,
    interest_rate NUMERIC(5,2),
    status        VARCHAR(20),
    branch_code   VARCHAR(10) NOT NULL
);

CREATE TABLE core_banking.deposits (
    deposit_id     SERIAL PRIMARY KEY,
    customer_id    INT REFERENCES core_banking.customers(customer_id),
    deposit_amount NUMERIC(15,2) NOT NULL,
    term_months    INT,
    status         VARCHAR(20),
    branch_code    VARCHAR(10) NOT NULL
);

INSERT INTO core_banking.customers (customer_id, full_name, phone_number, id_number, branch_code, balance) VALUES
(1, 'Nguyễn Văn An',    '0912345678', '001099012345', 'HN',  150000000),
(2, 'Trần Thị Bình',    '0987654321', '001099067890', 'HN',   85000000),
(3, 'Lê Hoàng Cường',   '0901234567', '079099011111', 'HCM', 320000000),
(4, 'Phạm Minh Đức',    '0938765432', '079099022222', 'HCM',  45000000),
(5, 'Võ Thị Lan',       '0905111222', '048099033333', 'DN',  200000000),
(6, 'Bùi Hữu Nghĩa',    '0911223344', '001099044444', 'HN',  500000000),
(7, 'Đặng Thu Thảo',    '0988776655', '079099055555', 'HCM', 120000000),
(8, 'Hồ Viết Châu',     '0909888777', '048099066666', 'DN',   15000000),
(9, 'Phan Tấn Phát',    '0977665544', '001099077777', 'HN',  250000000),
(10, 'Ngô Mai Phương',  '0966554433', '079099088888', 'HCM',  95000000);

SELECT setval('core_banking.customers_customer_id_seq', 10);

INSERT INTO core_banking.transactions (customer_id, amount, txn_type, txn_date, branch_code) VALUES
(1,  50000000, 'DEPOSIT',   '2024-01-15', 'HN'),
(1,  10000000, 'WITHDRAW',  '2024-02-20', 'HN'),
(2,  30000000, 'TRANSFER',  '2024-03-10', 'HN'),
(3, 100000000, 'DEPOSIT',   '2024-01-20', 'HCM'),
(4,   5000000, 'WITHDRAW',  '2024-04-05', 'HCM'),
(5,  75000000, 'DEPOSIT',   '2024-02-28', 'DN'),
(6, 200000000, 'DEPOSIT',   '2024-01-10', 'HN'),
(6,  15000000, 'TRANSFER',  '2024-03-05', 'HN'),
(7,  50000000, 'DEPOSIT',   '2024-02-15', 'HCM'),
(8,   2000000, 'WITHDRAW',  '2024-04-10', 'DN'),
(9, 100000000, 'DEPOSIT',   '2024-01-25', 'HN'),
(9,  20000000, 'WITHDRAW',  '2024-03-20', 'HN'),
(10, 30000000, 'DEPOSIT',   '2024-02-05', 'HCM'),
(10, 10000000, 'TRANSFER',  '2024-04-15', 'HCM'),
(1,  12000000, 'TRANSFER',  '2024-05-01', 'HN'),
(3,  50000000, 'WITHDRAW',  '2024-05-10', 'HCM');

INSERT INTO core_banking.loans (customer_id, loan_amount, interest_rate, status, branch_code) VALUES
(1, 500000000, 7.5, 'ACTIVE', 'HN'),
(3, 1200000000, 8.0, 'ACTIVE', 'HCM'),
(5, 300000000, 7.0, 'CLOSED', 'DN'),
(6, 800000000, 7.2, 'ACTIVE', 'HN'),
(7, 150000000, 8.5, 'ACTIVE', 'HCM'),
(9, 200000000, 7.8, 'CLOSED', 'HN');

INSERT INTO core_banking.deposits (customer_id, deposit_amount, term_months, status, branch_code) VALUES
(2, 200000000, 12, 'ACTIVE', 'HN'),
(4, 50000000, 6, 'MATURED', 'HCM'),
(5, 150000000, 24, 'ACTIVE', 'DN'),
(6, 500000000, 12, 'ACTIVE', 'HN'),
(8, 100000000, 6, 'ACTIVE', 'DN'),
(10, 300000000, 24, 'ACTIVE', 'HCM'),
(1, 100000000, 3, 'MATURED', 'HN'),
(3, 400000000, 12, 'ACTIVE', 'HCM');
"""


def seed_banking_tables():
    """Create core_banking schema + physical tables + sample data."""
    with engine.begin() as conn:
        for stmt in BANKING_DDL.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                conn.execute(text(stmt))
    print("✅ Banking tables seeded (10 customers, 16 transactions, 6 loans, 8 deposits)")


# ─── 2. Resource Catalog ─────────────────────────────────

def _ensure_resource(session, res_id, res_type):
    existing = session.get(Resource, res_id)
    if not existing:
        session.add(Resource(id=res_id, resource_type=res_type))
        session.flush()


def seed_resource_catalog(session):
    """Create 4-level resource catalog: DATABASE → SCHEMA → TABLE → COLUMN."""
    # DATABASE
    db_id = _id("db-seabank")
    _ensure_resource(session, db_id, "DATABASE")
    if not session.get(Database, db_id):
        session.add(Database(resource_id=db_id, name="governance_demo"))
    session.flush()

    # SCHEMA
    sch_id = _id("sch-core-banking")
    _ensure_resource(session, sch_id, "SCHEMA")
    if not session.get(Schema, sch_id):
        session.add(Schema(resource_id=sch_id, database_id=db_id, name="core_banking"))
    session.flush()

    # TABLES + COLUMNS
    tables = {
        "customers": [
            ("customer_id", "integer", True),
            ("full_name", "varchar", False),
            ("phone_number", "varchar", False),
            ("id_number", "varchar", False),
            ("branch_code", "varchar", False),
            ("balance", "numeric", False),
        ],
        "transactions": [
            ("txn_id", "integer", True),
            ("customer_id", "integer", False),
            ("amount", "numeric", False),
            ("txn_type", "varchar", False),
            ("txn_date", "date", False),
            ("branch_code", "varchar", False),
        ],
        "loans": [
            ("loan_id", "integer", True),
            ("customer_id", "integer", False),
            ("loan_amount", "numeric", False),
            ("interest_rate", "numeric", False),
            ("status", "varchar", False),
            ("branch_code", "varchar", False),
        ],
        "deposits": [
            ("deposit_id", "integer", True),
            ("customer_id", "integer", False),
            ("deposit_amount", "numeric", False),
            ("term_months", "integer", False),
            ("status", "varchar", False),
            ("branch_code", "varchar", False),
        ],
    }

    for tbl_name, columns in tables.items():
        tbl_id = _id(f"tbl-{tbl_name}")
        _ensure_resource(session, tbl_id, "TABLE")
        if not session.get(Table, tbl_id):
            session.add(Table(resource_id=tbl_id, schema_id=sch_id, name=tbl_name))
        session.flush()

        for col_name, dtype, is_pk in columns:
            col_id = _id(f"col-{tbl_name}-{col_name}")
            _ensure_resource(session, col_id, "COLUMN")
            if not session.get(ColumnResource, col_id):
                session.add(ColumnResource(
                    resource_id=col_id,
                    table_id=tbl_id,
                    name=col_name,
                    data_type=dtype,
                    is_primary_key=is_pk,
                ))
        session.flush()

    print("✅ Resource catalog seeded (1 DB → 1 Schema → 4 Tables → 24 Columns)")


# ─── 3. Users + Roles ────────────────────────────────────

def seed_identity(session):
    """Create 3 users, 3 roles, and link them."""
    roles = [
        (_id("role-teller"), "teller", "Giao dịch viên"),
        (_id("role-manager"), "branch_manager", "Giám đốc chi nhánh"),
        (_id("role-auditor"), "compliance_auditor", "Kiểm toán viên"),
    ]
    for rid, name, display in roles:
        if not session.get(Role, rid):
            session.add(Role(id=rid, name=name, display_name=display))
    session.flush()

    users = [
        (_id("user-teller"), "teller_hn", "Nguyễn Thị Hoa (GDV)", "HN", "role-teller"),
        (_id("user-manager"), "manager_hcm", "Trần Quốc Bảo (GĐ)", "HCM", "role-manager"),
        (_id("user-auditor"), "auditor", "Lê Minh Tuấn (KTV)", None, "role-auditor"),
    ]
    for uid, username, full_name, branch, role_key in users:
        if not session.get(User, uid):
            session.add(User(id=uid, username=username, full_name=full_name, branch_code=branch))
        session.flush()
        role_id = _id(role_key)
        existing = session.execute(
            select(UserRole).where(UserRole.user_id == uid, UserRole.role_id == role_id)
        ).scalar_one_or_none()
        if not existing:
            session.add(UserRole(user_id=uid, role_id=role_id))
    session.flush()

    print("✅ Identity seeded (3 users, 3 roles)")


# ─── 4. Permissions ───────────────────────────────────────

def _add_permission(session, perm_id, role_id, resource_id, effect,
                    row_filter_expr=None, mask_type=None, mask_pattern=None):
    """Create permission + optional row filter + optional column mask."""
    if not session.get(Permission, perm_id):
        session.add(Permission(
            id=perm_id,
            role_id=role_id,
            resource_id=resource_id,
            action="SELECT",
            effect=effect,
        ))
        session.flush()

    if row_filter_expr:
        existing_rf = session.execute(
            select(RowFilter).where(RowFilter.permission_id == perm_id)
        ).scalar_one_or_none()
        if not existing_rf:
            session.add(RowFilter(permission_id=perm_id, condition_expr=row_filter_expr))

    if mask_type:
        existing_cm = session.execute(
            select(ColumnMask).where(ColumnMask.permission_id == perm_id)
        ).scalar_one_or_none()
        if not existing_cm:
            session.add(ColumnMask(permission_id=perm_id, mask_type=mask_type, mask_pattern=mask_pattern))

    session.flush()


def seed_permissions(session):
    """Create the permission matrix for 3 roles."""
    teller = _id("role-teller")
    manager = _id("role-manager")
    auditor = _id("role-auditor")

    tbl_customers = _id("tbl-customers")
    tbl_transactions = _id("tbl-transactions")
    sch_core = _id("sch-core-banking")
    db_seabank = _id("db-seabank")
    col_phone = _id("col-customers-phone_number")
    col_idnum = _id("col-customers-id_number")
    col_balance = _id("col-customers-balance")
    tbl_loans = _id("tbl-loans")
    tbl_deposits = _id("tbl-deposits")
    col_loan_amount = _id("col-loans-loan_amount")
    col_deposit_amount = _id("col-deposits-deposit_amount")

    # ── TELLER: Row filter by branch, mask phone + id_number ──
    _add_permission(session, _id("perm-teller-customers"), teller, tbl_customers, "ALLOW",
                    row_filter_expr="branch_code = {user.branch_code}")
    _add_permission(session, _id("perm-teller-txn"), teller, tbl_transactions, "ALLOW",
                    row_filter_expr="branch_code = {user.branch_code}")
    _add_permission(session, _id("perm-teller-loans"), teller, tbl_loans, "ALLOW",
                    row_filter_expr="branch_code = {user.branch_code}")
    _add_permission(session, _id("perm-teller-deposits"), teller, tbl_deposits, "ALLOW",
                    row_filter_expr="branch_code = {user.branch_code}")
                    
    _add_permission(session, _id("perm-teller-phone"), teller, col_phone, "ALLOW",
                    mask_type="PARTIAL", mask_pattern="***")
    _add_permission(session, _id("perm-teller-idnum"), teller, col_idnum, "ALLOW",
                    mask_type="PARTIAL", mask_pattern="***")
    _add_permission(session, _id("perm-teller-balance"), teller, col_balance, "ALLOW",
                    mask_type="REDACT")
    _add_permission(session, _id("perm-teller-loan_amt"), teller, col_loan_amount, "ALLOW",
                    mask_type="REDACT")
    _add_permission(session, _id("perm-teller-dep_amt"), teller, col_deposit_amount, "ALLOW",
                    mask_type="REDACT")

    # ── BRANCH MANAGER: Row filter by branch, hash id_number ──
    _add_permission(session, _id("perm-mgr-schema"), manager, sch_core, "ALLOW",
                    row_filter_expr="branch_code = {user.branch_code}")
    _add_permission(session, _id("perm-mgr-idnum"), manager, col_idnum, "ALLOW",
                    mask_type="HASH")

    # ── COMPLIANCE AUDITOR: Full access at DATABASE level ──
    _add_permission(session, _id("perm-auditor-db"), auditor, db_seabank, "ALLOW")

    print("✅ Permissions seeded (teller: filter+mask, manager: filter+hash, auditor: full)")


# ─── Main ─────────────────────────────────────────────────

def main():
    print("\n🚀 Seeding AI Governance Demo...\n")

    # Create all ORM tables (resources, users, permissions, etc.)
    Base.metadata.create_all(bind=engine)
    print("✅ ORM tables created")

    # Seed physical banking data
    seed_banking_tables()

    # Seed catalog + identity + permissions
    session = SessionLocal()
    try:
        seed_resource_catalog(session)
        seed_identity(session)
        seed_permissions(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    print("\n🎉 Demo data seeded successfully!")
    print("   Run backend:  python main.py")
    print("   Users:        teller_hn | manager_hcm | auditor")
    print()


if __name__ == "__main__":
    main()
