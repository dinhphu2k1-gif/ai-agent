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

for select_expr in ast.expressions:
    # select_expr is usually an Alias or Column
    print("select_expr:", type(select_expr), repr(select_expr))
    if isinstance(select_expr, sqlglot.exp.Alias):
        col = select_expr.this
        if isinstance(col, sqlglot.exp.Column):
            print("  Column table:", col.table, "name:", col.name)
            # If denied:
            if col.name == "full_name":
                # Replace with NULL
                select_expr.set("this", sqlglot.parse_one("NULL"))

print("Rewritten:")
print(ast.sql(dialect="postgres"))
