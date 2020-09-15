import os
import uuid

from click.testing import CliRunner
import pytest
from sseclient import Event

from faculty_cli.cli import cli
from faculty.clients.account import AccountClient
from faculty.clients.template import TemplateClient
from faculty.clients.notification import (
    NotificationClient,
    PublishTemplateNotifications,
)

USER_ID = uuid.uuid4()
PROJECT_ID = uuid.uuid4()


def test_init():
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["template", "init"])
        assert result.exit_code == 0
        assert os.path.isfile("parameters.yaml")
        assert os.path.isdir("faculty-resources")
        assert os.path.isdir("workspace")


def test_publish_new_template_missing_project_id(mocker):
    mocker.patch.object(
        AccountClient, "authenticated_user_id", return_value=USER_ID
    )

    runner = CliRunner(mix_stderr=False, env={"FACULTY_PROJECT_ID": None})
    result = runner.invoke(cli, ["template", "publish", "new", "name"])

    assert result.exit_code >= 1
    assert (
        result.stderr
        == "This command is meant to be used from inside a Faculty server.\n"
    )


def test_publish_new_template_success(mocker):
    mocker.patch.object(
        AccountClient, "authenticated_user_id", return_value=USER_ID
    )
    mocker.patch("os.path.abspath", return_value="/project/src/")
    mock_notifications = mocker.Mock()
    get_notifications_mock = mocker.patch.object(
        NotificationClient,
        "get_publish_template_notifications",
        return_value=mock_notifications,
    )
    publish_new_mock = mocker.patch.object(TemplateClient, "publish_new")

    runner = CliRunner(
        mix_stderr=False, env={"FACULTY_PROJECT_ID": str(PROJECT_ID)}
    )
    result = runner.invoke(cli, ["template", "publish", "new", "name"])
    assert result.exit_code == 0
    assert result.stdout == "Successfully published template `name`.\n"

    get_notifications_mock.assert_called_once_with(USER_ID, PROJECT_ID)
    publish_new_mock.assert_called_once_with(PROJECT_ID, "name", "/src/")
    mock_notifications.wait_for_completion.assert_called_once_with()


@pytest.mark.parametrize(
    "input_src_dir, mock_abs_src_dir, expected_src_dir",
    [
        ("source/dir", "/project/source/dir", "/source/dir"),
        ("", "/project", "/"),
        ("", "/project/path", "/path"),
        (".", "/project", "/"),
        (".", "/project/path", "/path"),
        ("/project", "/project", "/"),
        ("/project/", "/project", "/"),
        ("/project/path", "/project/path", "/path"),
    ],
)
def test_publish_new_template_custom_source_dir(
    mocker, input_src_dir, mock_abs_src_dir, expected_src_dir
):
    mocker.patch.object(
        AccountClient, "authenticated_user_id", return_value=USER_ID
    )
    mocker.patch("os.path.abspath", return_value=mock_abs_src_dir)
    mock_notifications = mocker.Mock()
    get_notifications_mock = mocker.patch.object(
        NotificationClient,
        "get_publish_template_notifications",
        return_value=mock_notifications,
    )
    publish_new_mock = mocker.patch.object(TemplateClient, "publish_new")

    runner = CliRunner(
        mix_stderr=False, env={"FACULTY_PROJECT_ID": str(PROJECT_ID)}
    )
    result = runner.invoke(
        cli, ["template", "publish", "new", "name", input_src_dir]
    )
    assert result.exit_code == 0
    assert result.stdout == "Successfully published template `name`.\n"

    get_notifications_mock.assert_called_once_with(USER_ID, PROJECT_ID)
    publish_new_mock.assert_called_once_with(
        PROJECT_ID, "name", expected_src_dir
    )
    mock_notifications.wait_for_completion.assert_called_once_with()


def test_publish_new_template_outside_project(mocker):
    mocker.patch.object(
        AccountClient, "authenticated_user_id", return_value=USER_ID
    )
    mocker.patch("os.path.abspath", return_value="/outside/project")
    runner = CliRunner(
        mix_stderr=False, env={"FACULTY_PROJECT_ID": str(PROJECT_ID)}
    )
    result = runner.invoke(
        cli, ["template", "publish", "new", "name", "/outside/project"]
    )
    assert result.exit_code >= 1
    assert result.stderr == (
        "Source directory must be under /project. "
        "This command is meant to be used from inside a Faculty server.\n"
    )
