import sqlglot
from sqlglot.optimizer.qualify import qualify

schema = {
    "core_banking": {
        "customers": {"customer_id": "INT", "full_name": "VARCHAR", "id_number": "VARCHAR"}
    }
}
ast = sqlglot.parse_one("SELECT * FROM core_banking.customers WHERE id_number = '123'")
ast = qualify(ast, schema=schema)

for col in ast.find_all(sqlglot.exp.Column):
    if col.name == "id_number":
        col.replace(sqlglot.parse_one("NULL"))

print(ast.sql(dialect="postgres"))
