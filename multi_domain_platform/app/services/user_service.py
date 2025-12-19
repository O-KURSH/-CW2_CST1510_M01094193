import bcrypt
from app.data.users import get_user_by_username, insert_user


def register_user(username, password, role="user"):
    """
    Register a new user with a hashed password.

    Returns:
        (success: bool, message: str)
    """
    # 1) Check if username already exists
    existing = get_user_by_username(username)
    if existing is not None:
        return False, f"Username '{username}' already exists."

    # 2) Hash the password
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    # 3) Insert into the database
    insert_user(username, password_hash, role)

    return True, f"User '{username}' registered successfully."


def login_user(username, password):
    """
    Authenticate a user by username + password.

    Returns:
        (success: bool, message: str)
    """
    user = get_user_by_username(username)
    if not user:
        return False, "User not found."

    # user row = (id, username, password_hash, role)
    stored_hash = user[2]

    if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
        return True, "Login successful!"
    return False, "Incorrect password."