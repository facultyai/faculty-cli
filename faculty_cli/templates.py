"""Interact with the Faculty knowledge centre."""

# Copyright 2016-2019 Faculty Science Limited
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

import os

DUMMY_PARAMETERS_YAML = """
# This file describes the parameters used in the interpolation of your
# template. Each parameter has a name, description and type that help users of
# your template choose sensible values.

parameters:
  parameter_name:
    type: <str|bool|filename|number|subdomain>
    description: <Some text to help the user choose a suitable value>
    default: <Some sensible default value>
"""

DUMMY_RESOURCE_FILE = """
name: my-environment
description: My cool environment uses {{ parameter_name }}.
schemaVersion: v1
kind: environment
spec:
  bash:
  - script: |
     echo \"It also uses it here {{ parameter_name }}\"
"""


def create_blank_template():
    resource_path = os.path.join(os.getcwd(), "faculty-resources")
    workspace_path = os.path.join(os.getcwd(), "workspace")
    os.mkdir(resource_path)
    os.mkdir(workspace_path)

    def _write_yaml(yaml_content, path):
        with open(os.path.join(os.getcwd(), path), "w") as parameters:
            parameters.write(yaml_content)

    _write_yaml(DUMMY_PARAMETERS_YAML, "parameters.yaml")
    _write_yaml(
        DUMMY_RESOURCE_FILE, os.path.join(resource_path, "environment.yaml")
    )
