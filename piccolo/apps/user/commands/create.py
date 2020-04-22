import sys
from getpass import getpass

from piccolo.apps.user.tables import BaseUser


def create():
    """
    Create a new user.
    """
    username = input("Enter username:\n")
    email = input("Enter email:\n")

    password = getpass("Enter password:\n")
    confirmed_password = getpass("Confirm password:\n")

    if not password == confirmed_password:
        print("Passwords don't match!")
        sys.exit(1)

    while True:
        admin = input("Admin user? Enter y or n:\n")
        if admin in ("y", "n"):
            break
        else:
            print("Unrecognised option")

    is_admin = admin == "y"

    user = BaseUser(
        username=username,
        password=password,
        admin=is_admin,
        email=email,
        active=True,
    )
    user.save().run_sync()

    print(f"Created User {user.id}")
