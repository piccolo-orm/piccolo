import jinja2

TEMPLATE = """
ID = '{migration_id}'


{% if auto %}
from piccolo.migrations.auto import MigrationManager
{% endif %}

async def forwards():
    {% if auto %}
    manager = MigrationManager()

    {% for statement in alter_statements %}
    {{ alter_statement }}
    {% endfor %}

    return manager
    {% else %}
    pass
    {% endif %}


async def backwards():
    pass
"""


def render_template(**kwargs):
    template = jinja2.Template()

    return template.render(**kwargs)
