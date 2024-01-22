from piccolo.apps.user.tables import BaseUser
from piccolo.utils.printing import print_dict_table


def list_users():
    """
    List existing users.
    """
    users = (
        BaseUser.select(*BaseUser.all_columns(exclude=[BaseUser.password]))
        .order_by(BaseUser.username)
        .run_sync()
    )

    if len(users) < 1:
        print("No data")
        return

    print_dict_table(users)
