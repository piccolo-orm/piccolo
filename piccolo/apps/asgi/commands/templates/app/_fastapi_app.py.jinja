from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, status
from fastapi.exceptions import HTTPException
from piccolo.engine import engine_finder
from piccolo_admin.endpoints import create_admin
from piccolo_api.crud.serializers import create_pydantic_model
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from home.endpoints import HomeEndpoint
from home.piccolo_app import APP_CONFIG
from home.tables import Task


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


@asynccontextmanager
async def lifespan(app: FastAPI):
    await open_database_connection_pool()
    yield
    await close_database_connection_pool()


app = FastAPI(
    routes=[
        Route("/", HomeEndpoint),
        Mount(
            "/admin/",
            create_admin(
                tables=APP_CONFIG.table_classes,
                # Required when running under HTTPS:
                # allowed_hosts=['my_site.com']
            ),
        ),
        Mount("/static/", StaticFiles(directory="static")),
    ],
    lifespan=lifespan,
)


TaskModelIn: Any = create_pydantic_model(
    table=Task,
    model_name="TaskModelIn",
)

TaskModelOut: Any = create_pydantic_model(
    table=Task,
    include_default_columns=True,
    model_name="TaskModelOut",
)


# Check if the record is None. Use for query callback
def check_record_not_found(result: dict[str, Any]) -> dict[str, Any]:
    if result is None:
        raise HTTPException(
            detail="Record not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )
    return result


@app.get("/tasks/", response_model=list[TaskModelOut], tags=["Task"])
async def tasks():
    return await Task.select().order_by(Task._meta.primary_key, ascending=False)


@app.get("/tasks/{task_id}/", response_model=TaskModelOut, tags=["Task"])
async def single_task(task_id: int):
    task = (
        await Task.select()
        .where(Task._meta.primary_key == task_id)
        .first()
        .callback(check_record_not_found)
    )
    return task


@app.post("/tasks/", response_model=TaskModelOut, tags=["Task"])
async def create_task(task_model: TaskModelIn):
    task = Task(**task_model.model_dump())
    await task.save()
    return task.to_dict()


@app.put("/tasks/{task_id}/", response_model=TaskModelOut, tags=["Task"])
async def update_task(task_id: int, task_model: TaskModelIn):
    task = (
        await Task.objects()
        .get(Task._meta.primary_key == task_id)
        .callback(check_record_not_found)
    )
    for key, value in task_model.model_dump().items():
        setattr(task, key, value)

    await task.save()
    return task.to_dict()


@app.delete(
    "/tasks/{task_id}/",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Task"],
)
async def delete_task(task_id: int):
    task = (
        await Task.objects()
        .get(Task._meta.primary_key == task_id)
        .callback(check_record_not_found)
    )
    await task.remove()
