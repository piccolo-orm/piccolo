from piccolo.apps.user.tables import BaseUser
from piccolo.utils.printing import print_dict_table


def list_users(limit: int = 20, page: int = 1):
    """
    List existing users.

    :param limit:
        The maximum number of users to list.
    :param page:
        Lets you paginate through the list of users.

    """
    if page < 1:
        raise ValueError("The page number must > 0.")

    if limit < 1:
        raise ValueError("The limit number must be > 0.")

    users = (
        BaseUser.select(*BaseUser.all_columns(exclude=[BaseUser.password]))
        .order_by(BaseUser.username)
        .limit(limit)
        .offset(limit * (page - 1))
        .run_sync()
    )

    if len(users) == 0:
        print("No data")
        return

    print_dict_table(users, header_separator=True)
