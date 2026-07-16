"""Test memory API."""
import httpx, json, sys

# Login
r = httpx.post('http://localhost:8000/api/auth/login',
    json={'email': 'admin@brainagi.app', 'password': 'Admin@123456'})
data = r.json()
token = data['token']
print(f"Token: {token[:20]}...")

# Store memory
r2 = httpx.post('http://localhost:8000/api/memory/',
    json={'memory_type': 'semantic', 'title': 'Test memory', 'content': 'Testing memory storage'},
    headers={'Authorization': f'Bearer {token}'})
print(f"Store memory: {r2.status_code}")
print(f"Response: {r2.text[:300]}")

# List memories
r3 = httpx.get('http://localhost:8000/api/memory/',
    headers={'Authorization': f'Bearer {token}'})
print(f"\nList memories: {r3.status_code}")
memories = r3.json()
if memories:
    for m in memories[:3]:
        print(f"  - {m['title']} ({m['memory_type']})")
else:
    print("  (empty)")

# Test search
r4 = httpx.get('http://localhost:8000/api/memory/search?query=test',
    headers={'Authorization': f'Bearer {token}'})
print(f"\nSearch: {r4.status_code}")
print(r4.text[:500])
