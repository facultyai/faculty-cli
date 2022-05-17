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

from faculty_cli.parse import (
    parse_parameter_values,
    _escape_split,
    parse_run_identifier,
    RunIdentifier,
)


@pytest.mark.parametrize(
    "string, run_identifier",
    [("2.3", RunIdentifier(2, 3)), ("2", RunIdentifier(2, None))],
)
def test_parse_run_identifier(string, run_identifier):
    assert parse_run_identifier(string) == run_identifier


@pytest.mark.parametrize(
    "string", ["bad argument", "two.one", "2.one", "2.", "2.3.2", "1e3"]
)
def test_parse_run_identifier_bad_argument(string):
    with pytest.raises(ValueError, match="Invalid run identifier"):
        parse_run_identifier(string)


@pytest.mark.parametrize(
    "string, split_string",
    [
        (r"foo=eggs,bar=spam", ["foo=eggs", "bar=spam"]),
        ("foo", ["foo"]),
        (r"foo\,bar,eggs\,spam", ["foo,bar", "eggs,spam"]),
    ],
)
def test_escape_split(string, split_string):
    assert _escape_split(string, ",") == split_string


@pytest.mark.parametrize(
    "parameter_value_string, parameter_values",
    [
        ("foo=1,bar=2", {"foo": "1", "bar": "2"}),
        ("foo=1", {"foo": "1"}),
        ("foo=", {"foo": ""}),
        ("foo= bar ", {"foo": " bar "}),
        (r"spam=bar\=1,eggs=a\,2", {"spam": "bar=1", "eggs": "a,2"}),
        ("foo=1,", {"foo": "1"}),
        (",foo=1", {"foo": "1"}),
        ("foo=1,,bar=2", {"foo": "1", "bar": "2"}),
        ("", {}),
    ],
)
def test_parse_parameter_values(parameter_value_string, parameter_values):
    assert parse_parameter_values(parameter_value_string) == parameter_values


@pytest.mark.parametrize("parameter_value_string", ["foo", "foo==1"])
def test_parse_parameter_values_bad_argument(parameter_value_string):
    with pytest.raises(ValueError, match="Invalid parameter value"):
        parse_parameter_values(parameter_value_string)
