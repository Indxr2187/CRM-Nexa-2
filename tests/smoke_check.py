"""Manual route smoke check against the configured local database."""
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run import app

client = app.test_client()
page = client.get("/login")
assert page.status_code == 200
token = re.search(rb'name="csrf_token" value="([^"]+)"', page.data).group(1).decode()
response = client.post("/login", data={"csrf_token": token, "email": "admin@example.com", "password": "ChangeMe123!"}, follow_redirects=True)
assert response.status_code == 200 and b"Total customers" in response.data
paths = ("/customers", "/leads", "/pipeline", "/opportunities", "/followups", "/reports", "/employees", "/employees/1", "/opportunities/1")
for path in paths:
    result = client.get(path)
    assert result.status_code == 200, (path, result.status_code)
print(f"Real CSRF login and dashboard plus {len(paths)} authenticated pages: OK")

