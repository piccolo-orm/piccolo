import sys
from getpass import getpass, getuser

from piccolo.apps.user.tables import BaseUser


def get_username() -> str:
    default_username = getuser()
    username = input(f"Enter username ({default_username}):\n")
    return default_username if not username else username


def get_email() -> str:
    return input("Enter email:\n")


def get_password() -> str:
    return getpass("Enter password:\n")


def get_confirmed_password() -> str:
    return getpass("Confirm password:\n")


def get_is_admin() -> bool:
    while True:
        admin = input("Admin user? Enter y or n:\n")
        if admin in ("y", "n"):
            break
        else:
            print("Unrecognised option")

    return admin == "y"


def create():
    """
    Create a new user.
    """
    username = get_username()
    email = get_email()
    password = get_password()
    confirmed_password = get_confirmed_password()

    if not password == confirmed_password:
        sys.exit("Passwords don't match!")

    if len(password) < 4:
        sys.exit("The password is too short")

    is_admin = get_is_admin()

    user = BaseUser(
        username=username,
        password=password,
        admin=is_admin,
        email=email,
        active=True,
    )
    user.save().run_sync()

    print(f"Created User {user.id}")
