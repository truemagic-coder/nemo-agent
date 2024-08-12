from typing import Optional
from passlib.hash import pbkdf2_sha256

class User:
    def __init__(self, username: str, password: str):
        self.username = username
        self.hashed_password = pbkdf2_sha256.hash(password)
