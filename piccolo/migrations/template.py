import jinja2

TEMPLATE = """
ID = '{migration_id}'


async def forwards():
    pass


async def backwards():
    pass
"""


def render_template(**kwargs):
    template = jinja2.Template()

    return template.render(**kwargs)
