from database import SessionLocal
from models.identity import User
from services.filter_engine import filter_and_execute
import uuid

db = SessionLocal()
user = db.query(User).filter_by(id=uuid.UUID("12e2b613-cded-54fe-a579-4b592547c03b")).first()

sql = "SELECT t.txn_id, c.full_name, c.phone_number, t.amount, t.txn_type, t.txn_date, t.branch_code FROM core_banking.transactions t JOIN core_banking.customers c ON t.customer_id = c.customer_id"

try:
    result = filter_and_execute(sql, user, db)
    print("Rewritten SQL:\n", result.rewritten_sql)
    print("\nPolicy Applied:\n", result.policy)
    print("\nSample Rows:")
    for r in result.rows[:2]:
        print(r)
except Exception as e:
    import traceback
    traceback.print_exc()
