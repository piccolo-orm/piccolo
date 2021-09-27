import sys
import typing as t
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


def get_is_superuser() -> bool:
    while True:
        superuser = input("Superuser? Enter y or n:\n")
        if superuser in ("y", "n"):
            break
        else:
            print("Unrecognised option")

    return superuser == "y"


def get_is_active() -> bool:
    while True:
        active = input("Active? Enter y or n:\n")
        if active in ("y", "n"):
            break
        else:
            print("Unrecognised option")

    return active == "y"


def create(
    username: t.Optional[str] = None,
    email: t.Optional[str] = None,
    password: t.Optional[str] = None,
    is_admin: t.Optional[bool] = None,
    is_superuser: t.Optional[bool] = None,
    is_active: t.Optional[bool] = None,
):
    """
    Create a new user.
    """
    username = get_username() if username is None else username
    email = get_email() if email is None else email
    if password is None:
        password = get_password()
        confirmed_password = get_confirmed_password()

        if password != confirmed_password:
            sys.exit("Passwords don't match!")

    if len(password) < 4:
        sys.exit("The password is too short")

    is_admin = get_is_admin() if is_admin is None else is_admin
    is_superuser = get_is_superuser() if is_superuser is None else is_superuser
    is_active = get_is_active() if is_active is None else is_active

    user = BaseUser(
        username=username,
        password=password,
        admin=is_admin,
        email=email,
        active=is_active,
        superuser=is_superuser,
    )
    user.save().run_sync()

    print(f"Created User {user.id}")  # type: ignore
