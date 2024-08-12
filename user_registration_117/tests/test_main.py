"""
Tests for the User Registration and Login App
"""

import pytest
from user_registration_117.main import register_user, login_user

def test_register_user():
    email = "test@example.com"
    password = "password"

    assert email not in users
    register_user(email, password)
    assert email in users
    assert users[email] == hashlib.sha256(password.encode()).hexdigest()

def test_login_user_success():
    email = "test@example.com"
    password = "password"

    register_user(email, password)
    success, message = login_user(email, password)

    assert success is True
    assert message == "Login successful!"

def test_login_user_failure():
    email = "nonexistent@example.com"
    password = "wrong_password"

    success, message = login_user(email, password)

    assert success is False
    assert message == "Invalid credentials"
