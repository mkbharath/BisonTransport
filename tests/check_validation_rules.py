"""Check current validation rules and mandatory fields."""
import httpx
import json

API_BASE = "http://localhost:8000/api/v1"

res = httpx.post(f"{API_BASE}/auth/login", json={"email": "admin@test.com", "password": "admin123"})
token = res.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}

print("=== Business Rules ===")
res = httpx.get(f"{API_BASE}/admin/business-rules", headers=headers)
for r in res.json()["data"]:
    print(f"  {r['rule_name']:30} | type={r['rule_type']:15} | field={r['field_name']:20} | expr={r['rule_expression'][:40]:40} | severity={r['severity']}")

print("\n=== Field Configs ===")
res = httpx.get(f"{API_BASE}/admin/field-configs", headers=headers)
fields = res.json()["data"]
mandatory = [f for f in fields if f["is_mandatory"]]
conditional = [f for f in fields if f["is_conditional"]]
optional = [f for f in fields if not f["is_mandatory"] and not f["is_conditional"]]

print(f"\n  Mandatory fields ({len(mandatory)}):")
for f in mandatory:
    print(f"    {f['field_name']}")

print(f"\n  Conditional fields ({len(conditional)}):")
for f in conditional:
    print(f"    {f['field_name']} (depends on {f.get('conditional_depends_on', '?')}: {f.get('conditional_value', '?')})")

print(f"\n  Optional fields ({len(optional)}):")
for f in optional:
    print(f"    {f['field_name']}")
