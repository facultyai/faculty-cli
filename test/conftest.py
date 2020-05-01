import pytest

from test.fixtures import PROFILE, USER_ID


@pytest.fixture
def mock_profile(mocker):
    mocker.patch("faculty.config.resolve_profile", return_value=PROFILE)


@pytest.fixture
def mock_update_check(mocker):
    mocker.patch("faculty_cli.update.check_for_new_release")


@pytest.fixture
def mock_check_credentials(mocker):
    mocker.patch("faculty_cli.cli._check_credentials")


@pytest.fixture
def mock_user_id(mocker):
    mocker.patch(
        "faculty_cli.cli._get_authenticated_user_id", return_value=USER_ID
    )
