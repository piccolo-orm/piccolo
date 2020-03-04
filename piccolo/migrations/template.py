import jinja2


TEMPLATE = """
{% if auto %}
from piccolo.migrations.auto import MigrationManager


{% endif %}
ID = '{{ migration_id }}'


async def forwards():
    {% if auto %}
    manager = MigrationManager()
    {% for alter_statement in alter_statements %}
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
    template = jinja2.Template(TEMPLATE, trim_blocks=True, lstrip_blocks=True)
    return template.render(**kwargs)
