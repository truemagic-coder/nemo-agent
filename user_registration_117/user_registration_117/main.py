"""
User Registration and Login App

This Streamlit app allows users to register and login.
"""

import streamlit as st
import hashlib
from typing import Tuple

# Simple in-memory storage for users (email: password)
users = {}

def register_user(email: str, password: str) -> None:
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    users[email] = hashed_password

def login_user(email: str, password: str) -> Tuple[bool, str]:
    if email in users and hashlib.sha256(password.encode()).hexdigest() == users[email]:
        return True, "Login successful!"
    else:
        return False, "Invalid credentials"

def main():
    st.title("User Registration and Login")

    option = st.radio("Choose an option", ["Register", "Login"])

    if option == "Register":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        if st.button("Register"):
            if password != confirm_password:
                st.error("Passwords do not match.")
            else:
                register_user(email, password)
                st.success("Registration successful!")

    elif option == "Login":
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            success, message = login_user(email, password)
            if success:
                st.success(message)
            else:
                st.error(message)

if __name__ == "__main__":
    main()