import faculty_cli.config


def test_casebook_url(mock_profile):
    assert (
        faculty_cli.config.casebook_url()
        == "https://casebook.services.subdomain.my.faculty.ai"
    )


def test_hudson_url(mock_profile):
    assert (
        faculty_cli.config.hudson_url()
        == "https://hudson.services.subdomain.my.faculty.ai"
    )


def test_baskerville_url(mock_profile):
    assert (
        faculty_cli.config.baskerville_url()
        == "https://baskerville.services.subdomain.my.faculty.ai"
    )
