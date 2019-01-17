import pytest

import sherlockml.config

import sml.config


PROFILE = sherlockml.config.Profile(
    domain="services.subdomain.sherlockml.net",
    protocol="protocol",
    client_id="client id",
    client_secret="client secret",
)


@pytest.fixture
def mock_profile(mocker):
    mocker.patch("sherlockml.config.resolve_profile", return_value=PROFILE)


def test_casebook_url(mock_profile):
    assert (
        sml.config.casebook_url()
        == "protocol://casebook.services.subdomain.sherlockml.net"
    )


def test_hudson_url(mock_profile):
    assert (
        sml.config.hudson_url()
        == "protocol://hudson.services.subdomain.sherlockml.net"
    )


def test_galleon_url(mock_profile):
    assert (
        sml.config.galleon_url()
        == "protocol://galleon.services.subdomain.sherlockml.net"
    )


def test_baskerville_url(mock_profile):
    assert (
        sml.config.baskerville_url()
        == "protocol://baskerville.services.subdomain.sherlockml.net"
    )
