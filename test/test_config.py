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
