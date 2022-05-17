# Copyright 2016-2022 Faculty Science Limited
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
