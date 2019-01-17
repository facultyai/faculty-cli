import pytest

import faculty.config

import faculty_cli.config


PROFILE = faculty.config.Profile(
    domain="services.subdomain.my.faculty.ai",
    protocol="protocol",
    client_id="client id",
    client_secret="client secret",
)


@pytest.fixture
def mock_profile(mocker):
    mocker.patch("faculty.config.resolve_profile", return_value=PROFILE)


def test_casebook_url(mock_profile):
    assert (
        faculty_cli.config.casebook_url()
        == "protocol://casebook.services.subdomain.my.faculty.ai"
    )


def test_hudson_url(mock_profile):
    assert (
        faculty_cli.config.hudson_url()
        == "protocol://hudson.services.subdomain.my.faculty.ai"
    )


def test_galleon_url(mock_profile):
    assert (
        faculty_cli.config.galleon_url()
        == "protocol://galleon.services.subdomain.my.faculty.ai"
    )


def test_baskerville_url(mock_profile):
    assert (
        faculty_cli.config.baskerville_url()
        == "protocol://baskerville.services.subdomain.my.faculty.ai"
    )
