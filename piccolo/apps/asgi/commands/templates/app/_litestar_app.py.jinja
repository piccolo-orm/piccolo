import typing as t

from home.endpoints import home
from home.piccolo_app import APP_CONFIG
from home.tables import Task
from litestar import Litestar, asgi, delete, get, patch, post
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.exceptions import NotFoundException
from litestar.static_files import StaticFilesConfig
from litestar.template import TemplateConfig
from litestar.types import Receive, Scope, Send
from piccolo.engine import engine_finder
from piccolo.utils.pydantic import create_pydantic_model
from piccolo_admin.endpoints import create_admin

TaskModelIn: t.Any = create_pydantic_model(
    table=Task,
    model_name="TaskModelIn",
)
TaskModelOut: t.Any = create_pydantic_model(
    table=Task,
    include_default_columns=True,
    model_name="TaskModelOut",
)


# mounting Piccolo Admin
@asgi("/admin/", is_mount=True)
async def admin(scope: "Scope", receive: "Receive", send: "Send") -> None:
    await create_admin(tables=APP_CONFIG.table_classes)(scope, receive, send)


@get("/tasks", tags=["Task"])
async def tasks() -> t.List[TaskModelOut]:
    return await Task.select().order_by(Task.id, ascending=False)


@post("/tasks", tags=["Task"])
async def create_task(data: TaskModelIn) -> TaskModelOut:
    task = Task(**data.dict())
    await task.save()
    return task.to_dict()


@patch("/tasks/{task_id:int}", tags=["Task"])
async def update_task(task_id: int, data: TaskModelIn) -> TaskModelOut:
    task = await Task.objects().get(Task.id == task_id)
    if not task:
        raise NotFoundException("Task does not exist")
    for key, value in data.dict().items():
        setattr(task, key, value)

    await task.save()
    return task.to_dict()


@delete("/tasks/{task_id:int}", tags=["Task"])
async def delete_task(task_id: int) -> None:
    task = await Task.objects().get(Task.id == task_id)
    if not task:
        raise NotFoundException("Task does not exist")
    await task.remove()


async def open_database_connection_pool():
    try:
        engine = engine_finder()
        await engine.start_connection_pool()
    except Exception:
        print("Unable to connect to the database")


async def close_database_connection_pool():
    try:
        engine = engine_finder()
        await engine.close_connection_pool()
    except Exception:
        print("Unable to connect to the database")


app = Litestar(
    route_handlers=[
        admin,
        home,
        tasks,
        create_task,
        update_task,
        delete_task,
    ],
    template_config=TemplateConfig(
        directory="home/templates", engine=JinjaTemplateEngine
    ),
    static_files_config=[
        StaticFilesConfig(directories=["static"], path="/static/"),
    ],
    on_startup=[open_database_connection_pool],
    on_shutdown=[close_database_connection_pool],
)
