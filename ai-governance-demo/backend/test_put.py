import requests

url = "http://localhost:8000/api/admin/users/7a0615aa-0d61-4522-91ad-3f7590ef99e8/permissions"
payload = [
  {
    "resource_id": "72fa3c0a-a3b2-5773-a9b4-e5a3548c90c9",
    "resource_name": "core_banking",
    "resource_type": "SCHEMA",
    "effect": "ALLOW",
    "row_filter": None,
    "mask_type": None
  }
]
res = requests.put(url, json=payload)
print(res.status_code)
print(res.text)
