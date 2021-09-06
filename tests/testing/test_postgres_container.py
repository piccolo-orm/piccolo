import docker  # type: ignore

from tests.postgres_container import CONTAINER_IDENTIFIER, TestPostgres


def test_container_status():
    test_postgres = TestPostgres()
    client = docker.client.from_env()
    container_list = client.containers.list(
        filters={"label": f"test_container_identifier={CONTAINER_IDENTIFIER}"}
    )
    assert len(container_list) == 1

    test_postgres.tear_down()

    container_list = client.containers.list(
        filters={"label": f"test_container_identifier={CONTAINER_IDENTIFIER}"}
    )
    assert len(container_list) == 0
