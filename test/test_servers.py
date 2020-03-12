import pytest
from tabulate import tabulate
from click.testing import CliRunner

from faculty_cli.cli import cli, _server_spec

from faculty.clients.server import ServerClient
from test.fixtures import (
    PROJECT,
    SHARED_SERVER,
    DEDICATED_SERVER,
    DEDICATED_RESOURCE,
    SHARED_RESOURCE,
    USER_ID,
)


@pytest.fixture
def mock_update_check(mocker):
    mocker.patch("faculty_cli.update.check_for_new_release")


@pytest.fixture
def mock_check_credentials(mocker):
    mocker.patch("faculty_cli.cli._check_credentials")


@pytest.fixture
def mock_user_id(mocker):
    mocker.patch("faculty_cli.auth.user_id", return_value=USER_ID)


def test_list_all_servers(
    mocker,
    mock_update_check,
    mock_check_credentials,
    mock_profile,
    mock_user_id,
):
    runner = CliRunner()

    schema_mock = mocker.patch("faculty.clients.server.ServerSchema")
    mocker.patch.object(ServerClient, "_get", return_value=[DEDICATED_SERVER])
    mocker.patch("faculty_cli.cli._list_projects", return_value=[PROJECT])
    result = runner.invoke(cli, ["server", "list"])
    assert result.exit_code == 0
    assert (
        result.output
        == tabulate(
            [(PROJECT.name, DEDICATED_SERVER.name)],
            ("Project Name", "Server Name"),
            tablefmt="plain",
        )
        + "\n"
    )
    ServerClient._get.assert_called_once_with(
        "/instance/{}".format(PROJECT.id),
        schema_mock.return_value,
        params=None,
    )


def test_list_all_servers_verbose(
    mocker,
    mock_update_check,
    mock_check_credentials,
    mock_profile,
    mock_user_id,
):
    runner = CliRunner()

    schema_mock = mocker.patch("faculty.clients.server.ServerSchema")
    mocker.patch.object(ServerClient, "_get", return_value=[DEDICATED_SERVER])
    mocker.patch("faculty_cli.cli._list_projects", return_value=[PROJECT])
    result = runner.invoke(cli, ["server", "list", "--verbose"])
    assert result.exit_code == 0
    assert (
        result.output
        == tabulate(
            [
                (
                    PROJECT.name,
                    PROJECT.id,
                    DEDICATED_SERVER.name,
                    DEDICATED_SERVER.type,
                    DEDICATED_RESOURCE.node_type,
                    "-",
                    "-",
                    DEDICATED_SERVER.status.value,
                    DEDICATED_SERVER.id,
                    DEDICATED_SERVER.created_at.strftime("%Y-%m-%d %H:%M"),
                )
            ],
            (
                "Project Name",
                "Project ID",
                "Server Name",
                "Type",
                "Machine Type",
                "CPUs",
                "RAM",
                "Status",
                "Server ID",
                "Started",
            ),
            tablefmt="plain",
        )
        + "\n"
    )
    ServerClient._get.assert_called_once_with(
        "/instance/{}".format(PROJECT.id),
        schema_mock.return_value,
        params=None,
    )


def test_list_servers(
    mocker,
    mock_update_check,
    mock_check_credentials,
    mock_profile,
    mock_user_id,
):
    runner = CliRunner()

    schema_mock = mocker.patch("faculty.clients.server.ServerSchema")
    mocker.patch.object(ServerClient, "_get", return_value=[DEDICATED_SERVER])
    mocker.patch("faculty_cli.cli._resolve_project", return_value=PROJECT.id)
    result = runner.invoke(cli, ["server", "list", "{}".format(PROJECT.id)])
    assert result.exit_code == 0
    assert result.output == DEDICATED_SERVER.name + "\n"
    ServerClient._get.assert_called_once_with(
        "/instance/{}".format(PROJECT.id),
        schema_mock.return_value,
        params=None,
    )


def test_list_servers_verbose(
    mocker,
    mock_update_check,
    mock_check_credentials,
    mock_profile,
    mock_user_id,
):
    runner = CliRunner()

    schema_mock = mocker.patch("faculty.clients.server.ServerSchema")
    mocker.patch.object(ServerClient, "_get", return_value=[DEDICATED_SERVER])
    mocker.patch("faculty_cli.cli._resolve_project", return_value=PROJECT.id)
    result = runner.invoke(
        cli, ["server", "list", "{}".format(PROJECT.id), "--verbose"]
    )
    assert result.exit_code == 0
    assert (
        result.output
        == tabulate(
            [
                (
                    DEDICATED_SERVER.name,
                    DEDICATED_SERVER.type,
                    DEDICATED_RESOURCE.node_type,
                    "-",
                    "-",
                    DEDICATED_SERVER.status.value,
                    DEDICATED_SERVER.id,
                    DEDICATED_SERVER.created_at.strftime("%Y-%m-%d %H:%M"),
                )
            ],
            (
                "Server Name",
                "Type",
                "Machine Type",
                "CPUs",
                "RAM",
                "Status",
                "Server ID",
                "Started",
            ),
            tablefmt="plain",
        )
        + "\n"
    )

    ServerClient._get.assert_called_once_with(
        "/instance/{}".format(PROJECT.id),
        schema_mock.return_value,
        params=None,
    )


def test_server_spec_dedicated():
    machine_type, cpus, memory_gb = _server_spec(DEDICATED_SERVER)
    assert machine_type == DEDICATED_RESOURCE.node_type
    assert cpus == "-"
    assert memory_gb == "-"


def test_server_spec_shared():
    machine_type, cpus, memory_gb = _server_spec(SHARED_SERVER)
    assert machine_type == "-"
    assert cpus == "{:.3g}".format(SHARED_RESOURCE.milli_cpus / 1000)
    assert memory_gb == "{:.3g}GB".format(SHARED_RESOURCE.memory_mb / 1000)