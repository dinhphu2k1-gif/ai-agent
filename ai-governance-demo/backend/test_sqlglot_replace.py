import sqlglot
from sqlglot.optimizer.qualify import qualify

schema = {
    "core_banking": {
        "transactions": {"txn_id": "INT", "customer_id": "INT", "amount": "DECIMAL", "txn_type": "VARCHAR", "txn_date": "DATE", "branch_code": "VARCHAR"},
        "customers": {"customer_id": "INT", "full_name": "VARCHAR", "phone_number": "VARCHAR", "id_number": "VARCHAR", "branch_code": "VARCHAR", "balance": "DECIMAL"}
    }
}

ast = sqlglot.parse_one("SELECT t.txn_id, c.full_name, amount FROM core_banking.transactions t JOIN core_banking.customers c ON t.customer_id = c.customer_id")
ast = qualify(ast, schema=schema)

for table in ast.find_all(sqlglot.exp.Table):
    print("Found table:", table.db, table.name, table.alias_or_name)
    subq_sql = f"(SELECT * FROM {table.db}.{table.name} WHERE branch_code = 'DN')"
    subq = sqlglot.parse_one(subq_sql)
    subq_with_alias = sqlglot.exp.alias_(subq, table.alias_or_name)
    table.replace(subq_with_alias)

print("Rewritten:")
print(ast.sql(dialect="postgres"))
