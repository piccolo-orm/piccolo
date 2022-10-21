import os

import jinja2
from starlite import MediaType, Request, Response, get

ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(
        searchpath=os.path.join(os.path.dirname(__file__), "templates")
    )
)


@get(path="/", include_in_schema=False)
def home(request: Request) -> Response:
    template = ENVIRONMENT.get_template("home.html.jinja")
    content = template.render(title="Piccolo + ASGI")
    return Response(
        content,
        media_type=MediaType.HTML,
        status_code=200,
    )
