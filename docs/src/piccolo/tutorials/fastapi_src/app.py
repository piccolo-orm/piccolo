from fastapi import Depends, FastAPI
from pydantic import BaseModel

from piccolo.columns.column_types import Varchar
from piccolo.engine.sqlite import SQLiteEngine
from piccolo.table import Table

DB = SQLiteEngine()


class Band(Table, db=DB):
    """
    You would usually import this from tables.py
    """

    name = Varchar()


async def transaction():
    async with DB.transaction() as transaction:
        yield transaction


app = FastAPI()


@app.get("/bands/", dependencies=[Depends(transaction)])
async def get_bands():
    return await Band.select()


class CreateBandModel(BaseModel):
    name: str


@app.post("/bands/", dependencies=[Depends(transaction)])
async def create_band(model: CreateBandModel):
    await Band({Band.name: model.name}).save()

    # If an exception is raised then the transaction is rolled back.
    raise Exception("Oops")


async def main():
    await Band.create_table(if_not_exists=True)


if __name__ == "__main__":
    import asyncio

    import uvicorn

    asyncio.run(main())
    uvicorn.run(app)
