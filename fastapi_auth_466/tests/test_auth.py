# ... previous tests ...

def test_register_invalid_username():
    response = client.post("/register", json"})
    assert response.status_code == 400

def test_register_duplicate_user():
    # Create user first
    client.post("/register", json"})
    response = client.post("/register", json"})
    assert response.status_code == 400

# ... more tests ...
