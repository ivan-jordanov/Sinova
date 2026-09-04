"""Quick test of implemented features."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_operations_list():
    """Test GET /preprocessing/operations."""
    response = client.get("/api/v1/preprocessing/operations")
    assert response.status_code == 200
    ops = response.json()
    assert len(ops) > 0
    # Check structure
    op = ops[0]
    assert "id" in op
    assert "name" in op
    assert "short_name" in op
    assert "requires" in op
    print("✓ GET /preprocessing/operations works")
    print(f"  Available: {[o['short_name'] for o in ops]}")


def test_valid_operation_order():
    """Test valid operation sequence."""
    response = client.post(
        "/api/v1/preprocessing/apply",
        json={
            "configuration": {
                "operations": [
                    {
                        "id": "1",
                        "name": "Normalize",
                        "short_name": "normalize",
                        "category": "intensity",
                        "description": "",
                        "enabled": True,
                        "scope": "slice",
                        "parameters": {},
                    },
                    {
                        "id": "2",
                        "name": "Negative Log",
                        "short_name": "negative_log",
                        "category": "intensity",
                        "description": "",
                        "enabled": True,
                        "scope": "slice",
                        "parameters": {},
                    },
                ]
            }
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "queued"
    print("✓ POST /preprocessing/apply (valid order) works")
    print(f"  Response: {data['message']}")


def test_invalid_operation_order():
    """Test invalid operation sequence."""
    response = client.post(
        "/api/v1/preprocessing/apply",
        json={
            "configuration": {
                "operations": [
                    {
                        "id": "2",
                        "name": "Negative Log",
                        "short_name": "negative_log",
                        "category": "intensity",
                        "description": "",
                        "enabled": True,
                        "scope": "slice",
                        "parameters": {},
                    },
                    {
                        "id": "1",
                        "name": "Normalize",
                        "short_name": "normalize",
                        "category": "intensity",
                        "description": "",
                        "enabled": True,
                        "scope": "slice",
                        "parameters": {},
                    },
                ]
            }
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert "requires" in data["detail"] or "must come after" in data["detail"]
    print("✓ POST /preprocessing/apply (invalid order) rejected")
    print(f"  Error: {data['detail']}")


def test_load_invalid_path():
    """Test that invalid path is rejected."""
    response = client.post(
        "/api/v1/ingestion/load",
        json={"path": "/etc/passwd"},
    )
    assert response.status_code == 400
    data = response.json()
    assert "whitelisted" in data["detail"] or "not found" in data["detail"]
    print("✓ POST /ingestion/load (invalid path) rejected")
    print(f"  Error: {data['detail']}")


if __name__ == "__main__":
    print("Testing implemented features...\n")
    test_operations_list()
    test_valid_operation_order()
    test_invalid_operation_order()
    test_load_invalid_path()
    print("\n✓ All tests passed!")
