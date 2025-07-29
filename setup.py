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

import os.path

from setuptools import find_packages, setup


def source_root_dir():
    """Return the path to the root of the source distribution."""
    return os.path.abspath(os.path.dirname(__file__))


def read_long_description():
    """Read from the README file in root of source directory."""
    readme = os.path.join(source_root_dir(), "README.md")
    with open(readme) as fin:
        return fin.read()


setup(
    name="faculty-cli",
    description="The command line interface to Faculty",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://faculty.ai/platform/",
    author="Faculty",
    author_email="opensource@faculty.ai",
    license="Apache Software License",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Operating System :: POSIX",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
    ],
    keywords="data science platform",
    packages=find_packages(),
    setup_requires=["setuptools_scm"],
    python_requires=">=3.9",
    install_requires=[
        "click",
        "python-dateutil",
        "requests",
        "tabulate",
        "faculty>=0.31.0",
        # TODO: setuptools is required to supply `distutils`
        # until we remove that dependency in the code
        "setuptools",
    ],
    entry_points={"console_scripts": ["faculty=faculty_cli.cli:cli"]},
)
