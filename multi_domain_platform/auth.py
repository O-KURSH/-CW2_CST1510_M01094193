import bcrypt
import os

USER_DATA_FILE = "users.txt"


# -----------------------------
# PASSWORD FUNCTIONS
# -----------------------------

def hash_password(plain_text_password):
    password_bytes = plain_text_password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    return hashed_password.decode('utf-8')


def verify_password(plain_text_password, stored_hash):
    password_bytes = plain_text_password.encode('utf-8')
    stored_hash_bytes = stored_hash.encode('utf-8')
    return bcrypt.checkpw(password_bytes, stored_hash_bytes)


# -----------------------------
# USER CHECKING FUNCTION
# -----------------------------

def user_exists(username):
    # If the file doesn't exist, then no users exist yet
    if not os.path.exists(USER_DATA_FILE):
        return False

    with open(USER_DATA_FILE, "r") as f:
        for line in f:
            stored_username, _ = line.strip().split(",", 1)
            if stored_username == username:
                return True

    return False


# -----------------------------
# USER REGISTRATION
# -----------------------------

def register_user(username, password):
    # 1. Check if the username already exists
    if user_exists(username):
        print("Error: Username already exists.")
        return False

    # 2. Hash the password
    hashed_password = hash_password(password)

    # 3. Save username and hashed password to users.txt
    with open(USER_DATA_FILE, "a") as f:
        f.write(f"{username},{hashed_password}\n")

    print("Registration successful!")
    return True


# -----------------------------
# USER LOGIN
# -----------------------------

def login_user(username, password):
    # 1. Handle case where no users exist yet
    if not os.path.exists(USER_DATA_FILE):
        print("Error: No users registered yet.")
        return False  # No users registered → login fails

    # 2. Search for the username in the file
    with open(USER_DATA_FILE, "r") as f:
        for line in f:
            stored_username, stored_hash = line.strip().split(",", 1)

            # If username matches, verify the password
            if stored_username == username:
                if verify_password(password, stored_hash):
                    return True  # Login successful
                else:
                    print("Error: Incorrect password.")
                    return False  # Wrong password

    # 3. Username not found in the file
    print("Error: Username not found.")
    return False


# -----------------------------
# VALIDATION FUNCTIONS
# -----------------------------

def validate_username(username):
    """Returns (is_valid: bool, error_message: str)."""
    if len(username) < 3:
        return False, "Username must be at least 3 characters long."
    if "," in username:
        return False, "Username cannot contain commas."
    return True, ""


def validate_password(password):
    """Returns (is_valid: bool, error_message: str)."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    return True, ""


# -----------------------------
# MENU + MAIN LOOP
# -----------------------------

def display_menu():
    """Displays the main menu options."""
    print("\n" + "=" * 50)
    print(" MULTI-DOMAIN INTELLIGENCE PLATFORM")
    print(" Secure Authentication System")
    print("=" * 50)
    print("\n[1] Register a new user")
    print("[2] Login")
    print("[3] Exit")
    print("-" * 50)


def main():
    """Main program loop."""
    print("\nWelcome to the Week 7 Authentication System!")

    while True:
        display_menu()
        choice = input("\nPlease select an option (1-3): ").strip()

        if choice == '1':
            # Registration flow
            print("\n--- USER REGISTRATION ---")
            username = input("Enter a username: ").strip()

            # Validate username
            is_valid, error_msg = validate_username(username)
            if not is_valid:
                print(f"Error: {error_msg}")
                continue

            password = input("Enter a password: ").strip()

            # Validate password
            is_valid, error_msg = validate_password(password)
            if not is_valid:
                print(f"Error: {error_msg}")
                continue

            # Confirm password
            password_confirm = input("Confirm password: ").strip()
            if password != password_confirm:
                print("Error: Passwords do not match.")
                continue

            # Register the user
            register_user(username, password)

        elif choice == '2':
            # Login flow
            print("\n--- USER LOGIN ---")
            username = input("Enter your username: ").strip()
            password = input("Enter your password: ").strip()

            # Attempt login
            if login_user(username, password):
                print("\nYou are now logged in.")
                print("(In a real application, you would now access the dashboard or protected features.)")

                # Optional: Ask if they want to logout or exit
                input("\nPress Enter to return to main menu...")

        elif choice == '3':
            # Exit
            print("\nThank you for using the authentication system.")
            print("Exiting...")
            break

        else:
            print("\nError: Invalid option. Please select 1, 2, or 3.")


if __name__ == "__main__":
    main()