import sqlglot
from sqlglot.optimizer.qualify import qualify

schema = {
    "core_banking": {
        "transactions": {"txn_id": "INT", "customer_id": "INT", "amount": "DECIMAL", "txn_type": "VARCHAR", "txn_date": "DATE", "branch_code": "VARCHAR"},
        "customers": {"customer_id": "INT", "full_name": "VARCHAR", "phone_number": "VARCHAR", "id_number": "VARCHAR", "branch_code": "VARCHAR", "balance": "DECIMAL"}
    }
}

ast = sqlglot.parse_one("SELECT t.txn_id, c.full_name, amount FROM core_banking.transactions t JOIN core_banking.customers c ON t.customer_id = c.customer_id")
try:
    ast = qualify(ast, schema=schema)
    print(ast.sql())
except Exception as e:
    print("Error:", e)

ast2 = sqlglot.parse_one("SELECT * FROM core_banking.transactions t")
try:
    ast2 = qualify(ast2, schema=schema)
    print(ast2.sql())
except Exception as e:
    print("Error2:", e)
