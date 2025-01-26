import asyncio
import importlib
import sys
import typing as t

from httpx import ASGITransport, AsyncClient
from uvicorn import Config, Server


async def dummy_server(app: t.Union[str, t.Callable] = "app:app") -> None:
    """
    A very simplistic ASGI server. It's used to run the generated ASGI
    applications in unit tests.

    :param app:
        Either an ASGI app, or a string representing the path to an ASGI app.
        For example, ``module_1.app:app`` which would import an ASGI app called
        ``app`` from ``module_1.app``.

    """
    print("Running dummy server ...")

    if isinstance(app, str):
        path, app_name = app.rsplit(":")
        module = importlib.import_module(path)
        app = t.cast(t.Callable, getattr(module, app_name))

    try:
        async with AsyncClient(transport=ASGITransport(app=app)) as client:
            response = await client.get("http://localhost:8000")
            if response.status_code != 200:
                sys.exit("The app isn't callable!")
    except Exception:
        config = Config(app=app)
        server = Server(config=config)
        asyncio.create_task(server.serve())
        await asyncio.sleep(0.1)


if __name__ == "__main__":
    asyncio.run(dummy_server())
