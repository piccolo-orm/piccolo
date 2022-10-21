import os

import jinja2
from starlette.endpoints import HTTPEndpoint
from starlette.responses import HTMLResponse


ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        searchpath=os.path.join(os.path.dirname(__file__), "templates")
    )
)


class HomeEndpoint(HTTPEndpoint):
    async def get(self, request):
        template = ENVIRONMENT.get_template("home.html.jinja")

        content = template.render(title="Piccolo + ASGI",)

        return HTMLResponse(content)
