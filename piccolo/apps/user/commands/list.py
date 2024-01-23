import typing as t

from piccolo.apps.user.tables import BaseUser
from piccolo.columns import Column
from piccolo.utils.printing import print_dict_table

ORDER_BY_COLUMN_NAMES = [
    i._meta.name for i in BaseUser.all_columns(exclude=[BaseUser.password])
]


async def get_users(
    order_by: Column, ascending: bool, limit: int, page: int
) -> t.List[t.Dict[str, t.Any]]:
    return (
        await BaseUser.select(
            *BaseUser.all_columns(exclude=[BaseUser.password])
        )
        .order_by(
            order_by,
            ascending=ascending,
        )
        .limit(limit)
        .offset(limit * (page - 1))
    )


async def list_users(
    limit: int = 20, page: int = 1, order_by: str = "username"
):
    """
    List existing users.

    :param limit:
        The maximum number of users to list.
    :param page:
        Lets you paginate through the list of users.
    :param order_by:
        The column used to order the results. Prefix with '-' for descending
        order.

    """
    if page < 1:
        raise ValueError("The page number must > 0.")

    if limit < 1:
        raise ValueError("The limit number must be > 0.")

    ascending = True
    if order_by.startswith("-"):
        ascending = False
        order_by = order_by[1:]

    if order_by not in ORDER_BY_COLUMN_NAMES:
        raise ValueError(
            "The order_by argument must be one of the following: "
            + ", ".join(ORDER_BY_COLUMN_NAMES)
        )

    users = await get_users(
        order_by=BaseUser._meta.get_column_by_name(order_by),
        ascending=ascending,
        limit=limit,
        page=page,
    )

    if len(users) == 0:
        print("No data")
        return

    print_dict_table(users, header_separator=True)
