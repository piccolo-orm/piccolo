import jinja2


TEMPLATE = """
from piccolo.migrations.auto import MigrationManager


ID = '{{ migration_id }}'


async def forwards():
    manager = MigrationManager(migration_id=ID)
    {% if auto %}
    {% for alter_statement in alter_statements %}
    {{ alter_statement }}
    {% endfor %}
    {% else %}
    def run():
        print(f"running {ID}")

    manager.add_raw(run)
    {% endif %}
    return manager


async def backwards():
    pass

"""


def render_template(**kwargs):
    template = jinja2.Template(TEMPLATE, trim_blocks=True, lstrip_blocks=True)
    return template.render(**kwargs)
