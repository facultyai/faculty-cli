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


def test_dataset_get_source_not_found(mocker, mock_resolve_project):

    mocker.patch(
        "faculty.datasets.get",
        side_effect=faculty.datasets.util.DatasetsError(
            "No such object missing-source in project {}".format(
                mock_resolve_project.return_value
            )
        ),
    )

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "get", "test-project", "missing-source", "dest"]
    )

    assert result.exit_code == 64
    assert (
        result.output
        == "No such object missing-source in project test-project\n"
    )


@pytest.mark.parametrize(
    "exception", [FileNotFoundError, NotADirectoryError, OSError]
)
def test_dataset_get_bad_request(mocker, mock_resolve_project, exception):

    mocker.patch("faculty.datasets.get", side_effect=exception)

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "get", "test-project", "source", "dest"]
    )

    assert result.exit_code == 64


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


def test_dataset_put_dest_already_exists(mocker, mock_resolve_project):

    exception = faculty.clients.object.PathAlreadyExists("dest")
    mocker.patch("faculty.datasets.put", side_effect=exception)

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "put", "test-project", "source", "dest"]
    )

    assert result.exit_code == 64
    assert result.output == "{}\n".format(exception)


def test_dataset_put_source_not_found(mocker, mock_resolve_project):

    exception = FileNotFoundError(
        "[Errno 2] No such file or directory: 'source'"
    )
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


def test_dataset_cp_source_not_found(mocker, mock_resolve_project):

    exception = faculty.clients.object.PathNotFound("source")
    mocker.patch("faculty.datasets.cp", side_effect=exception)

    runner = CliRunner()
    result = runner.invoke(
        cli, ["dataset", "cp", "test-project", "source", "dest"]
    )

    assert result.exit_code == 64
    assert result.output == "{}\n".format(exception)


def test_dataset_cp_source_is_directory(mocker, mock_resolve_project):

    exception = faculty.clients.object.SourceIsADirectory("source-directory")
    mocker.patch("faculty.datasets.cp", side_effect=exception)

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "dataset",
            "cp",
            "test-project",
            "source-directory",
            "dest-directory",
        ],
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


def test_dataset_rm_object_not_found(mocker, mock_resolve_project):

    exception = faculty.clients.object.PathNotFound("object")
    mocker.patch("faculty.datasets.rm", side_effect=exception)

    runner = CliRunner()
    result = runner.invoke(cli, ["dataset", "rm", "test-project", "object"])

    assert result.exit_code == 64
    assert result.output == "{}\n".format(exception)


def test_dataset_rm_object_is_directory(mocker, mock_resolve_project):

    exception = faculty.clients.object.TargetIsADirectory("directory")
    mocker.patch("faculty.datasets.rm", side_effect=exception)

    runner = CliRunner()
    result = runner.invoke(cli, ["dataset", "rm", "test-project", "directory"])

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
