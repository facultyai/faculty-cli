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

import pytest
from click.testing import CliRunner

from faculty_cli.cli import cli
from faculty.clients.project import ProjectClient
import faculty.clients.base
from test.fixtures import PROJECT, USER_ID


@pytest.fixture
def mock_update_check(mocker):
    mocker.patch("faculty_cli.update.check_for_new_release")


@pytest.fixture
def mock_check_credentials(mocker):
    mocker.patch("faculty_cli.cli._check_credentials")


def test_list_projects(
    mocker,
    mock_update_check,
    mock_check_credentials,
    mock_profile,
    mock_user_id,
):
    runner = CliRunner()
    mocker.patch.object(
        ProjectClient, "list_accessible_by_user", return_value=[PROJECT]
    )

    result = runner.invoke(cli, ["project", "list"])

    assert result.exit_code == 0
    assert result.output == PROJECT.name + "\n"

    ProjectClient.list_accessible_by_user.assert_called_once_with(USER_ID)


def test_list_projects_verbose(
    mocker,
    mock_update_check,
    mock_check_credentials,
    mock_profile,
    mock_user_id,
):
    runner = CliRunner()
    mocker.patch.object(
        ProjectClient, "list_accessible_by_user", return_value=[PROJECT]
    )

    result = runner.invoke(cli, ["project", "list", "-v"])

    tpl = "Project Name    ID\n{}    {}\n"

    assert result.exit_code == 0
    assert result.output == tpl.format(PROJECT.name, PROJECT.id)

    ProjectClient.list_accessible_by_user.assert_called_once_with(USER_ID)


def test_create_project(
    mocker,
    mock_update_check,
    mock_check_credentials,
    mock_profile,
    mock_user_id,
):
    runner = CliRunner()

    mocker.patch.object(ProjectClient, "create", return_value=PROJECT)
    result = runner.invoke(cli, ["project", "new", "test-project"])

    assert result.exit_code == 0
    assert result.output == "Created project {} with ID {}\n".format(
        PROJECT.name, PROJECT.id
    )

    ProjectClient.create.assert_called_once_with(USER_ID, "test-project")


def test_create_project_bad_request(
    mocker,
    mock_update_check,
    mock_check_credentials,
    mock_profile,
    mock_user_id,
):
    runner = CliRunner()
    response = faculty.clients.base.BadRequest("response", error="some error")
    mocker.patch.object(ProjectClient, "create", side_effect=response)

    result = runner.invoke(cli, ["project", "new", "test-project"])

    assert result.exit_code == 64
    assert result.output == "some error\n"
