import pytest
from click.testing import CliRunner

import faculty.datasets
from faculty_cli.cli import cli
from test.fixtures import PROJECT


@pytest.fixture
def mock_resolve_project(mocker):
    return mocker.patch(
        "faculty_cli.cli._resolve_project", return_value=PROJECT.id
    )


def test_dataset_get(mocker, mock_resolve_project):

    mock_get = mocker.patch("faculty.datasets.get")

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "get", "test-project", "source", "dest"]
    )
    assert result.exit_code == 0

    mock_resolve_project.assert_called_once_with("test-project")
    mock_get.assert_called_once_with(
        "source", "dest", project_id=mock_resolve_project.return_value
    )


@pytest.mark.parametrize(
    "exception, message",
    [
        (
            faculty.datasets.util.DatasetsError(
                "No such object source in project {}".format(PROJECT.id)
            ),
            "No such object source in project test-project",
        ),
        (
            OSError("[Errno 2] No such file or directory: 'dest'"),
            "[Errno 2] No such file or directory: 'dest'",
        ),
    ],
)
def test_dataset_get_exception(
    mocker, mock_resolve_project, exception, message
):

    mocker.patch("faculty.datasets.get", side_effect=exception)

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "get", "test-project", "source", "dest"]
    )

    assert result.exit_code == 64
    assert result.output == "{}\n".format(message)


def test_dataset_put(mocker, mock_resolve_project):

    mock_put = mocker.patch("faculty.datasets.put")

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "put", "test-project", "source", "dest"]
    )
    assert result.exit_code == 0

    mock_resolve_project.assert_called_once_with("test-project")
    mock_put.assert_called_once_with(
        "source", "dest", project_id=mock_resolve_project.return_value
    )


@pytest.mark.parametrize(
    "exception",
    [
        faculty.clients.object.PathAlreadyExists("dest"),
        OSError("[Errno 2] No such file or directory: 'source'"),
    ],
)
def test_dataset_put_exception(mocker, mock_resolve_project, exception):

    mocker.patch("faculty.datasets.put", side_effect=exception)

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "put", "test-project", "source", "dest"]
    )

    assert result.exit_code == 64
    assert result.output == "{}\n".format(exception)


def test_dataset_mv(mocker, mock_resolve_project):

    mock_mv = mocker.patch("faculty.datasets.mv")

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "mv", "test-project", "source", "dest"]
    )
    assert result.exit_code == 0

    mock_resolve_project.assert_called_once_with("test-project")
    mock_mv.assert_called_once_with(
        "source", "dest", project_id=mock_resolve_project.return_value
    )


def test_dataset_mv_source_not_found(mocker, mock_resolve_project):

    exception = faculty.clients.object.PathNotFound("source")
    mocker.patch("faculty.datasets.mv", side_effect=exception)

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "mv", "test-project", "source", "dest"]
    )

    assert result.exit_code == 64
    assert result.output == "{}\n".format(exception)


def test_dataset_cp(mocker, mock_resolve_project):

    mock_cp = mocker.patch("faculty.datasets.cp")

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "cp", "test-project", "source", "dest"]
    )
    assert result.exit_code == 0

    mock_resolve_project.assert_called_once_with("test-project")
    mock_cp.assert_called_once_with(
        "source",
        "dest",
        project_id=mock_resolve_project.return_value,
        recursive=False,
    )


def test_dataset_cp_recursive(mocker, mock_resolve_project):

    mock_cp = mocker.patch("faculty.datasets.cp")

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "dataset",
            "cp",
            "test-project",
            "source-directory",
            "dest-directory",
            "--recursive",
        ],
    )
    assert result.exit_code == 0

    mock_resolve_project.assert_called_once_with("test-project")
    mock_cp.assert_called_once_with(
        "source-directory",
        "dest-directory",
        project_id=mock_resolve_project.return_value,
        recursive=True,
    )


@pytest.mark.parametrize(
    "exception",
    [
        faculty.clients.object.PathNotFound("source"),
        faculty.clients.object.SourceIsADirectory("source"),
    ],
)
def test_dataset_cp_exception(mocker, mock_resolve_project, exception):

    mocker.patch("faculty.datasets.cp", side_effect=exception)

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "cp", "test-project", "source", "dest"]
    )

    assert result.exit_code == 64
    assert result.output == "{}\n".format(exception)


def test_dataset_rm(mocker, mock_resolve_project):

    mock_rm = mocker.patch("faculty.datasets.rm")

    runner = CliRunner()
    result = runner.invoke(cli, ["dataset", "rm", "test-project", "object"])
    assert result.exit_code == 0

    mock_resolve_project.assert_called_once_with("test-project")
    mock_rm.assert_called_once_with(
        "object", project_id=mock_resolve_project.return_value, recursive=False
    )


def test_dataset_rm_recursive(mocker, mock_resolve_project):

    mock_rm = mocker.patch("faculty.datasets.rm")

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "rm", "test-project", "directory", "--recursive"]
    )
    assert result.exit_code == 0

    mock_resolve_project.assert_called_once_with("test-project")
    mock_rm.assert_called_once_with(
        "directory",
        project_id=mock_resolve_project.return_value,
        recursive=True,
    )


@pytest.mark.parametrize(
    "exception",
    [
        faculty.clients.object.PathNotFound("object"),
        faculty.clients.object.TargetIsADirectory("object"),
    ],
)
def test_dataset_rm_exception(mocker, mock_resolve_project, exception):

    exception = faculty.clients.object.PathNotFound("object")
    mocker.patch("faculty.datasets.rm", side_effect=exception)

    runner = CliRunner()
    result = runner.invoke(cli, ["dataset", "rm", "test-project", "object"])

    assert result.exit_code == 64
    assert result.output == "{}\n".format(exception)


def test_dataset_ls(mocker, mock_resolve_project):

    mock_ls = mocker.patch(
        "faculty.datasets.ls",
        return_value=["/", "/first-object", "/second-object"],
    )

    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["dataset", "ls", "test-project", "--prefix", "/", "--show-hidden"],
    )

    assert result.exit_code == 0
    assert result.stdout == "/\n/first-object\n/second-object\n"

    mock_resolve_project.assert_called_once_with("test-project")
    mock_ls.assert_called_once_with(
        "/", project_id=mock_resolve_project.return_value, show_hidden=True
    )
