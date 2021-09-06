import asyncio
import logging
import os
from contextlib import suppress
from typing import Union
import socket

import asyncpg  # type: ignore
import docker  # type: ignore
from docker.errors import APIError, NullResource  # type: ignore
from docker.models.containers import Container  # type: ignore
from faker import Faker

PG_DOCKER_IMAGE_NAME = os.environ.get("PG_DOCKER_IMAGE_NAME", "postgres")

fake = Faker()

TEST_CONTAINER_IDENTIFIER = "7F71F5AB-E255-4E76-B650-3F1EE64B2E36"


class TestPostgres:
    def __init__(self):
        self.docker_client = docker.client.from_env()
        self.resource_postfix = fake.color_name().lower()
        self.config = {
            "host": os.environ.get("PG_HOST", "localhost"),
            "port": os.environ.get("PG_PORT", 5432),
            "user": os.environ.get("PG_USER", "postgres"),
            "password": os.environ.get("PG_PASSWORD", fake.password()),
            "database": os.environ.get("PG_DATABASE", "piccolo"),
        }

    @property
    def port_is_free(self) -> bool:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((self.config['host'], self.config['port']))
        sock.close()
        return result != 0

    @property
    def container(self) -> Union[Container, None]:
        with suppress(NullResource):
            return self.docker_client.containers.get(
                container_id=self.container_name
            )

    @property
    def container_name(self) -> str:
        test_container = self.docker_client.containers.list(
            filters={"label": f"test_container_identifier={TEST_CONTAINER_IDENTIFIER}"}
        )
        if len(test_container) == 1:
            return test_container[0].name

    async def create_piccolo_database(self) -> None:
        """
        Executes a query.
        It waits until the database is ready first.
        """
        is_ready_exit_code = 1
        while is_ready_exit_code != 0:
            is_ready_exit_code = self.container.exec_run(
                cmd="pg_isready"
            ).exit_code
            await asyncio.sleep(1)

        connection = await asyncpg.connect(
            host=self.config["host"],
            port=self.config["port"],
            user=self.config["user"],
            password=self.config["password"],
        )
        query = f"create database {self.config['database']}"
        await connection.execute(query=query)
        await connection.close()

    def spin_up(self):
        if not self.port_is_free:
            raise OSError(f"Something is already running in port {self.config['port']}.")
        self.start_container()
        asyncio.get_event_loop().run_until_complete(
            self.create_piccolo_database()
        )

    def start_container(self) -> str:
        """
        Spins up a postgres docker container
        """
        try:
            logging.info(f"Pulling {PG_DOCKER_IMAGE_NAME}")
            self.docker_client.images.get(name=PG_DOCKER_IMAGE_NAME)
            logging.info(
                f"Starting container postgres-{self.resource_postfix}"
            )

            postgres_container = self.docker_client.containers.run(
                image=PG_DOCKER_IMAGE_NAME,
                ports={
                    f"{self.config['port']}/tcp": f"{self.config['port']}/tcp"
                },
                name=f"postgres-{self.resource_postfix}",
                hostname="postgres",
                environment={
                    "POSTGRES_PASSWORD": self.config["password"],
                    "POSTGRES_HOST_AUTH_METHOD": "trust",
                },
                labels={"test_container_identifier": TEST_CONTAINER_IDENTIFIER},
                detach=True,
                auto_remove=True,
            )
        except APIError as error:
            if error.status_code == 500:
                raise APIError(f"Something is already running in port {self.config['port']}.")
            else:
                raise APIError(error)

        return postgres_container.name

    def tear_down(self) -> None:
        try:
            self.container.remove(force=True)
        except AttributeError:
            logging.warning("Nothing to tear down.")
