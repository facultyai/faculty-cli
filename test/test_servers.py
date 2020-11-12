# Copyright 2016-2020 Faculty Science Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from click.testing import CliRunner

from faculty_cli.cli import cli, _server_spec

from faculty.clients.server import ServerClient
from test.fixtures import (
    PROJECT,
    SHARED_SERVER,
    DEDICATED_SERVER,
    DEDICATED_RESOURCE,
    SHARED_RESOURCE,
)


def test_no_servers_verbose(
    mocker,
    mock_update_check,
    mock_check_credentials,
    mock_profile,
    mock_user_id,
):
    runner = CliRunner()
    mocker.patch("faculty_cli.cli._list_projects", return_value=[PROJECT])
    mocker.patch("faculty_cli.cli._list_user_servers", return_value=[])
    mocker.patch.object(ServerClient, "_get", return_value=[])
    result = runner.invoke(cli, ["server", "list", "-v"])
    assert result.exit_code == 0
    assert result.output == "No servers.\n"


def test_list_all_servers_no_servers(
    mocker,
    mock_update_check,
    mock_check_credentials,
    mock_profile,
    mock_user_id,
):
    runner = CliRunner()
    mocker.patch("faculty_cli.cli._list_projects", return_value=[PROJECT])
    mocker.patch("faculty_cli.cli._list_user_servers", return_value=[])
    result = runner.invoke(cli, ["server", "list"])
    assert result.exit_code == 0
    assert result.output == ""


def test_list_all_servers(
    mocker,
    mock_update_check,
    mock_check_credentials,
    mock_profile,
    mock_user_id,
):
    runner = CliRunner()
    mocker.patch("faculty_cli.cli._list_projects", return_value=[PROJECT])
    mocker.patch(
        "faculty_cli.cli._list_user_servers", return_value=[DEDICATED_SERVER]
    )
    result = runner.invoke(cli, ["server", "list"])
    assert result.exit_code == 0
    assert result.output == DEDICATED_SERVER.name + "\n"


def test_list_all_servers_verbose(
    mocker,
    mock_update_check,
    mock_check_credentials,
    mock_profile,
    mock_user_id,
):
    runner = CliRunner()
    mocker.patch("faculty_cli.cli._list_projects", return_value=[PROJECT])
    mocker.patch(
        "faculty_cli.cli._list_user_servers", return_value=[DEDICATED_SERVER]
    )
    tabulate = mocker.patch("faculty_cli.cli.tabulate")

    result = runner.invoke(cli, ["server", "list", "--verbose"])
    assert result.exit_code == 0
    tabulate.assert_called_once_with(
        [
            (
                PROJECT.name,
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


def test_list_servers(
    mocker,
    mock_update_check,
    mock_check_credentials,
    mock_profile,
    mock_user_id,
):
    runner = CliRunner()
    mocker.patch(
        "faculty_cli.cli._get_servers", return_value=[DEDICATED_SERVER]
    )
    mocker.patch("faculty_cli.cli._resolve_project", return_value=PROJECT.id)
    result = runner.invoke(cli, ["server", "list", "{}".format(PROJECT.id)])
    assert result.exit_code == 0
    assert result.output == DEDICATED_SERVER.name + "\n"


def test_list_servers_verbose(
    mocker,
    mock_update_check,
    mock_check_credentials,
    mock_profile,
    mock_user_id,
):
    runner = CliRunner()
    mocker.patch(
        "faculty_cli.cli._get_servers", return_value=[DEDICATED_SERVER]
    )
    mocker.patch("faculty_cli.cli._resolve_project", return_value=PROJECT.id)
    tabulate = mocker.patch("faculty_cli.cli.tabulate")
    result = runner.invoke(
        cli, ["server", "list", "{}".format(PROJECT.id), "--verbose"]
    )
    assert result.exit_code == 0
    tabulate.assert_called_once_with(
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
