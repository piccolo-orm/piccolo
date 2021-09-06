from tests.postgres_container import TestPostgres, TEST_CONTAINER_IDENTIFIER
import docker


def test_container_status():
    test_postgres = TestPostgres()
    client = docker.client.from_env()
    container_list = client.containers.list(
            filters={"label": f"test_container_identifier={TEST_CONTAINER_IDENTIFIER}"}
        )
    assert len(container_list) == 1

    test_postgres.tear_down()

    container_list = client.containers.list(
            filters={"label": f"test_container_identifier={TEST_CONTAINER_IDENTIFIER}"}
        )
    assert len(container_list) == 0
