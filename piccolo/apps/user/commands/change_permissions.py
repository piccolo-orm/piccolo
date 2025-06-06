from typing import TYPE_CHECKING, Optional, Union

from piccolo.apps.user.tables import BaseUser
from piccolo.utils.warnings import Level, colored_string

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns import Column


async def change_permissions(
    username: str,
    admin: Optional[bool] = None,
    superuser: Optional[bool] = None,
    active: Optional[bool] = None,
):
    """
    Change a user's permissions.

    :param username:
        Change the permissions for this user.
    :param admin:
        Set `admin` for the user (true / false).
    :param superuser:
        Set `superuser` for the user (true / false).
    :param active:
        Set `active` for the user (true / false).

    """
    if not await BaseUser.exists().where(BaseUser.username == username).run():
        print(
            colored_string(
                f"User {username} doesn't exist!", level=Level.medium
            )
        )
        return

    params: dict[Union[Column, str], bool] = {}

    if admin is not None:
        params[BaseUser.admin] = admin

    if superuser is not None:
        params[BaseUser.superuser] = superuser

    if active is not None:
        params[BaseUser.active] = active

    if params:
        await BaseUser.update(params).where(
            BaseUser.username == username
        ).run()
    else:
        print(colored_string("No changes detected", level=Level.medium))
        return

    print(f"Updated permissions for {username}")
