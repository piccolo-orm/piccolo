import sys
from getpass import getpass

from piccolo.apps.user.tables import BaseUser


def change_password():
    """
    Change a user's password.
    """
    username = input("Enter username:\n")

    password = getpass("Enter password:\n")
    confirmed_password = getpass("Confirm password:\n")

    if not password == confirmed_password:
        print("Passwords don't match!")
        sys.exit(1)

    BaseUser.update_password_sync(user=username, password=password)

    print(f"Updated password for {username}")
    print(
        "If using session auth, we recommend invalidating this user's session."
    )
