import asyncio
import importlib
import sys
import typing as t


def dummy_server(app: t.Union[str, t.Callable] = "app:app"):
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
        app = getattr(module, app_name)

    async def send(message):
        if message["type"] == "http.response.start":
            if message["status"] == 200:
                print("Received 200")
            else:
                sys.exit("200 not received from app")

    async def receive():
        pass

    scope = {
        "scheme": "http",
        "type": "http",
        "path": "/",
        "raw_path": b"/",
        "method": "GET",
        "query_string": b"",
        "headers": [],
        "_body": b"null",
    }
    if callable(app):
        asyncio.run(app(scope, receive, send))
        print("Exiting dummy server ...")
    else:
        sys.exit("The app isn't callable!")


if __name__ == "__main__":
    dummy_server()
