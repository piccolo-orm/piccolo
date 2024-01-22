from piccolo.apps.user.tables import BaseUser
from piccolo.utils.printing import print_dict_table


def list():
    """
    List existing users.
    """
    users = (
        BaseUser.select(BaseUser.all_columns(exclude=[BaseUser.password]))
        .order_by(BaseUser.username)
        .run_sync()
    )

    print_dict_table(users)
