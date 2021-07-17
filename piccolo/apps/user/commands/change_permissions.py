import typing as t

from piccolo.apps.user.tables import BaseUser
from piccolo.utils.warnings import Level, colored_string

if t.TYPE_CHECKING:
    from piccolo.columns import Column


async def change_permissions(
    username: str,
    admin: t.Optional[bool] = None,
    superuser: t.Optional[bool] = None,
    active: t.Optional[bool] = None,
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

    params: t.Dict[t.Union[Column, str], bool] = {}

    if admin is not None:
        params[BaseUser.admin] = admin

    if superuser is not None:
        params[BaseUser.superuser] = superuser

    if active is not None:
        params[BaseUser.active] = active

    await BaseUser.update(params).where(BaseUser.username == username).run()

    print(f"Updated permissions for {username}")
