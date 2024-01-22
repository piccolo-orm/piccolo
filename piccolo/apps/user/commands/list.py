from piccolo.apps.user.tables import BaseUser
from piccolo.utils.printing import print_dict_table


def list_users(limit: int = 20):
    """
    List existing users.

    :param limit:
        The maximum number of users to list.

    """
    users = (
        BaseUser.select(*BaseUser.all_columns(exclude=[BaseUser.password]))
        .order_by(BaseUser.username)
        .limit(limit)
        .run_sync()
    )

    if len(users) == 0:
        print("No data")
        return

    print_dict_table(users, header_separator=True)
