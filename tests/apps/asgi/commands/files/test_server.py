import asyncio
import importlib
import signal
import sys
import typing as t
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from httpx import ASGITransport, AsyncClient
from uvicorn import Config, Server


# Implementation based on code in Uvicorn tests
# https://github.com/encode/uvicorn/blob/master/tests/utils.py
@asynccontextmanager
async def run_integration_server(config: Config) -> AsyncIterator[Server]:
    server = Server(config=config)
    task = asyncio.create_task(server.serve())
    await asyncio.sleep(0.1)
    try:
        yield server
    finally:
        await server.shutdown()
        task.cancel()


async def test_server(app: t.Union[str, t.Callable] = "app:app") -> None:
    """
    Uvicorn ASGI server. It's used to run the generated ASGI
    applications in unit tests.

    :param app:
        Either an ASGI app, or a string representing the path to an ASGI app.
        For example, ``module_1.app:app`` which would import an ASGI app called
        ``app`` from ``module_1.app``.

    """
    print("Running test server ...")

    if isinstance(app, str):
        path, app_name = app.rsplit(":")
        module = importlib.import_module(path)
        app = t.cast(t.Callable, getattr(module, app_name))

    config = Config(app=app, timeout_graceful_shutdown=1)
    async with run_integration_server(config) as server:
        async with AsyncClient(transport=ASGITransport(app=app)) as client:
            response = await client.get("http://localhost:8000")
            await asyncio.sleep(0.1)
            # exit from the server after successfully launching the app
            server.handle_exit(sig=signal.SIGINT, frame=None)
            if response.status_code != 200:
                sys.exit("The app isn't callable!")


if __name__ == "__main__":
    asyncio.run(test_server())
