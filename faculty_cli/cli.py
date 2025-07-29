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

"""Command line interface."""

import contextlib
import operator
import os
import os.path
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import time
import uuid
from distutils.version import StrictVersion
import click
import faculty
import faculty.config
import requests
import faculty.clients.base
import faculty.datasets
from faculty.clients.server import (
    DedicatedServerResources,
    ServerStatus,
    SharedServerResources,
)
from faculty.clients.serveragent import ServerAgentClient
from faculty.session import get_session
from tabulate import tabulate

import faculty_cli.parse
import faculty_cli.shell
import faculty_cli.update
import faculty_cli.version


SSH_OPTIONS = [
    "-o",
    "IdentitiesOnly=yes",
    "-o",
    "StrictHostKeyChecking=no",
    "-o",
    "BatchMode=yes",
]


class AmbiguousNameError(Exception):
    """Exception when name matches multiple resources."""

    pass


class NameNotFoundError(Exception):
    """Exception when a resource name is not found."""

    pass


def _print_and_exit(msg, code):
    """Print error message and exit with given code."""
    click.echo(msg, err=True)
    sys.exit(code)


def _get_pypi_versions():
    """List releases available from PyPI."""
    response = requests.get(
        "https://pypi.org/pypi/faculty-cli/json", timeout=1
    )
    versions = response.json()["releases"].keys()
    return [StrictVersion(v) for v in versions]


def _populate_creds_file():
    """Prompt user for client ID and secret and save them."""
    while True:
        domain = click.prompt(
            "Domain", default=faculty.config.DEFAULT_DOMAIN, err=True
        )
        client_id = click.prompt("Client ID", err=True).strip()
        client_secret = click.prompt("Client secret", err=True).strip()

        profile = faculty.config.Profile(
            domain=domain,
            protocol=faculty.config.DEFAULT_PROTOCOL,
            client_id=client_id,
            client_secret=client_secret,
        )
        session = faculty.session.Session(
            profile, faculty.session.accesstoken.AccessTokenMemoryCache()
        )

        try:
            session.access_token()
        except Exception:
            click.echo("Invalid credentials. Please try again.", err=True)
        else:
            break

    credentials = textwrap.dedent(
        """\
        [{profile}]
        domain = {domain}
        client_id = {client_id}
        client_secret = {client_secret}
        """.format(
            profile=faculty.config.DEFAULT_PROFILE,
            client_id=client_id,
            client_secret=client_secret,
            domain=domain,
        )
    )
    credentials_file = faculty.config.resolve_credentials_path()
    try:
        os.makedirs(os.path.dirname(credentials_file))
    except OSError:
        pass
    with open(credentials_file, "w") as creds_file:
        creds_file.write(credentials)
    os.chmod(
        credentials_file,
        stat.S_IRUSR | stat.S_IWUSR & ~stat.S_IRGRP & ~stat.S_IROTH,
    )


def _check_creds_file_perms():
    """Check the permissions of the credentials file are correct."""
    credentials_file = faculty.config.resolve_credentials_path()
    if oct(os.stat(credentials_file).st_mode & 0o777)[-2:] != "00":
        msg = textwrap.dedent(
            """\
        Permissions for {0} are too open.
        Your credentials file must not be accessible to other users on this
        computer.
        Run 'chmod 0600 {0}' to fix this.""".format(
                credentials_file
            )
        )
        _print_and_exit(msg, 66)


def _ensure_creds_file_present():
    """Ensure the user's credentials file is present."""
    credentials_file = faculty.config.resolve_credentials_path()
    try:
        open(credentials_file)
    except IOError:
        msg = textwrap.dedent(
            """\
        It looks like this is the first time you've used the Faculty CLI on
        this computer, so you must enter your Faculty credentials. They'll be
        saved so you don't have to enter them again.
        """
        )
        click.echo(msg, err=True)
        _populate_creds_file()


def _check_credentials():
    """Check if credentials are present in environment or config file."""
    try:
        faculty.config.resolve_profile()
    except faculty.config.CredentialsError:
        _ensure_creds_file_present()
        _check_creds_file_perms()


def _get_authenticated_user_id():
    client = faculty.client("account")
    return client.authenticated_user_id()


def _list_projects():
    """List all projects accessible by user."""
    client = faculty.client("project")
    user_id = _get_authenticated_user_id()
    projects = client.list_accessible_by_user(user_id)
    return projects


def _match_project(project):
    """Find a project by matching its name."""
    projects = _list_projects()
    matching_projects = [p for p in projects if p.name == project]
    if len(matching_projects) == 1:
        project = matching_projects[0]
    else:
        if not matching_projects:
            msg = 'no project of name "{}" found'.format(project)
            raise NameNotFoundError(msg)
        else:
            msg = (
                'more than one project of name "{}", please select by '
                "project ID instead"
            ).format(project)
            raise AmbiguousNameError(msg)
    return project.id


def _resolve_project(project):
    """Resolve a project name or ID to a project ID."""
    try:
        project_id = uuid.UUID(project)
    except ValueError:
        project_id = _match_project(project)
    return project_id


def _get_servers(project_id, name=None, status=None):
    """List servers in the given project."""
    client = faculty.client("server")
    servers = client.list(project_id, name)
    if status is not None:
        servers = [s for s in servers if s.status == status]
    return servers


def _list_user_servers(user_id, status=None):
    """List all servers owned by user."""
    client = faculty.client("server")
    servers = client.list_for_user(user_id)
    if status is not None:
        servers = [s for s in servers if s.status == status]
    return servers


def _server_by_name(project_id, server_name, status=None):
    """Resolve a project ID and server name to a server ID."""
    servers = _get_servers(project_id, server_name, status)

    if len(servers) == 1:
        return servers[0]
    else:
        adjective = "available" if status is None else status.value
        if not servers:
            msg = 'no {} server of name "{}" in this project'.format(
                adjective, server_name
            )
            raise NameNotFoundError(msg)
        else:
            msg = (
                'more than one {} server of name "{}", please select by '
                "server ID instead"
            ).format(adjective, server_name)
            raise AmbiguousNameError(msg)


def _any_server(project_id, status=None):
    """Get any server from project."""
    servers = _get_servers(project_id, status=status)
    if not servers:
        adjective = "available" if status is None else status.value
        _print_and_exit("No {} server in project.".format(adjective), 78)
    return servers[0].id


def _resolve_server(project, server=None, ensure_running=True):
    """Resolve project and server names to project and server IDs."""
    project_id = _resolve_project(project)
    status = ServerStatus.RUNNING if ensure_running else None
    try:
        server_id = uuid.UUID(server)
    except ValueError:
        server_id = _server_by_name(project_id, server, status).id
    except TypeError:
        server_id = _any_server(project_id, status)
    return project_id, server_id


def _server_spec(server):
    """Return formatted strings for machine type, cpu and memory of server."""
    if isinstance(server.resources, SharedServerResources):
        machine_type = "-"
        cpus = "{:.3g}".format(server.resources.milli_cpus / 1000)
        memory_gb = "{:.3g}GB".format(server.resources.memory_mb / 1000)
    else:
        machine_type = server.resources.node_type
        cpus = "-"
        memory_gb = "-"
    return machine_type, cpus, memory_gb


def _get_ssh_details(project, server):
    project_id, server_id = _resolve_server(project, server)
    client = faculty.client("server")
    return client.get_ssh_details(project_id, server_id)


def _job_by_name(project_id, job_name):
    """Resolve a project ID and job name to a job ID."""
    client = faculty.client("job")
    jobs = client.list(project_id)
    matching_jobs = [job for job in jobs if job.metadata.name == job_name]
    if len(matching_jobs) == 1:
        return matching_jobs[0]
    else:
        if not matching_jobs:
            msg = 'no job of name "{}" in this project'.format(job_name)
            raise NameNotFoundError(msg)
        else:
            msg = (
                'more than one job of name "{}", please select by job ID '
                "instead"
            ).format(job_name)
            raise AmbiguousNameError(msg)


def _resolve_job(project, job):
    """Resolve project and job names to project and job IDs."""
    project_id = _resolve_project(project)
    try:
        job_id = uuid.UUID(job)
    except ValueError:
        job_id = _job_by_name(project_id, job).id
    return project_id, job_id


def _environment_by_name(project_id, environment_name):
    client = faculty.client("environment")
    environments = client.list(project_id)
    matching_environments = [
        e for e in environments if e.name == environment_name
    ]
    if len(matching_environments) == 1:
        return matching_environments[0]
    else:
        if not matching_environments:
            msg = 'no available environment of name "{}"'.format(
                environment_name
            )
            raise NameNotFoundError(msg)
        else:
            msg = (
                'more than one environment of name "{}", please select by '
                "environment ID instead"
            ).format(environment_name)
            raise AmbiguousNameError(msg)


def _resolve_environment(project_id, environment):
    """Resolve environment to environment IDs."""
    try:
        environment_id = uuid.UUID(environment)
    except ValueError:
        environment_id = _environment_by_name(project_id, environment).id
    return environment_id


@contextlib.contextmanager
def _save_key_to_file(key):
    tmpdir = tempfile.mkdtemp()
    filename = os.path.join(tmpdir, "key.pem")
    with open(filename, "w") as keyfile:
        keyfile.write(key)
    os.chmod(filename, stat.S_IRUSR & ~stat.S_IRGRP & ~stat.S_IROTH)
    yield filename
    shutil.rmtree(tmpdir)


PERMISSION_DENIED_MESSAGE = """
Permission was denied when attempting to connect to your Faculty server. A
bug in earlier versions of OpenSSH (including the version distributed with
macOS 10.10) may be the cause - please try updating your operating system or
SSH version and try again.
""".replace(
    "\n", " "
).strip()


def _run_ssh_cmd(argv):
    """Run a command and print a message when a string is matched."""
    process = subprocess.Popen(argv, stderr=subprocess.PIPE)
    line = process.stderr.readline()
    while line:
        click.echo(line, nl=False, err=True)
        if (
            b"Permission denied" in line
            and b"rsync: send_files failed to open" not in line
        ):
            click.echo(PERMISSION_DENIED_MESSAGE, err=True)
        line = process.stderr.readline()
    return process.wait()


def _format_datetime(timestamp):
    if timestamp is None:
        return "-"
    else:
        return timestamp.strftime("%Y-%m-%d %H:%M")


class FacultyCLIGroup(click.Group):
    def __call__(self, *args, **kwargs):
        try:
            super(FacultyCLIGroup, self).__call__(*args, **kwargs)
        except AmbiguousNameError as err:
            _print_and_exit(err, 64)
        except NameNotFoundError as err:
            _print_and_exit(err, 64)


@click.group(cls=FacultyCLIGroup)
@click.version_option(
    version=faculty_cli.version.__version__, prog_name="faculty-cli"
)
def cli():
    """Command line interface to Faculty."""
    try:
        faculty_cli.update.check_for_new_release()
    except Exception:  # pylint: disable=broad-except
        pass


@cli.command()
def version():
    """Print the faculty_cli version number."""
    click.echo(faculty_cli.version.__version__)


@cli.command()
def login():
    """Write Faculty credentials to file."""
    credentials_file = faculty.config.resolve_credentials_path()
    if os.path.exists(credentials_file):
        if not click.confirm("Overwrite existing credentials file?"):
            return
    _populate_creds_file()


@cli.group()
def project():
    """Manipulate Faculty projects."""
    pass


@project.command(name="list")
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Print extra information about projects.",
)
def list_projects(verbose):
    """List accessible Faculty projects."""
    _check_credentials()
    projects = _list_projects()
    if verbose:
        if not projects:
            click.echo("No projects.")
        else:
            click.echo(
                tabulate(
                    [(p.name, p.id) for p in projects],
                    ("Project Name", "ID"),
                    tablefmt="plain",
                )
            )
    else:
        for project in projects:
            click.echo(project.name)


@project.command(name="new")
@click.argument("name")
def new_project(name):
    """Create new project."""
    client = faculty.client("project")
    user_id = _get_authenticated_user_id()
    try:
        returned_project = client.create(user_id, name)
    except faculty.clients.base.BadRequest as err:
        _print_and_exit(err.error, 64)
    click.echo(
        "Created project {} with ID {}".format(
            returned_project.name, returned_project.id
        )
    )


@cli.group()
def server():
    """Manipulate Faculty servers."""
    pass


@server.command(name="list")
@click.argument("project", required=False, metavar="PROJECT")
@click.option(
    "-a",
    "--all",
    is_flag=True,
    help="Show all servers, not just running ones.",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="",
)
@click.option(
    "-f",
    "--format",
    type=click.Choice(["list", "table", "ssh-config"], case_sensitive=False),
    help="Output format.",
)
def list_servers(project, all, verbose, format):
    """List your Faculty servers.

    If you do not specify a project, all servers will be listed."""
    if verbose:
        if format is None:
            # Retain legacy behaviour for verbose flag.
            format = "table"
        else:
            raise click.exceptions.BadOptionUsage(
                "format",
                "You can't specify the `--verbose` flag and also pass the "
                "`--format` option",
            )

    status_filter = None if all else ServerStatus.RUNNING
    if not project:
        projects = {project.id: project.name for project in _list_projects()}
        user_id = _get_authenticated_user_id()
        servers = [
            (projects[server.project_id], server)
            for server in _list_user_servers(user_id, status=status_filter)
        ]
    else:
        project_id = _resolve_project(project)
        servers = [
            ("", server)
            for server in _get_servers(project_id, status=status_filter)
        ]

    status_filter = None if all else ServerStatus.RUNNING
    headers = (
        "Project Name",
        "Server Name",
        "Type",
        "Machine Type",
        "CPUs",
        "RAM",
        "Status",
        "Server ID",
        "Started",
    )
    found_servers = []
    for project_name, server in servers:
        machine_type, cpus, memory_gb = _server_spec(server)
        found_servers.append(
            (
                project_name,
                server.name,
                server.type,
                machine_type,
                cpus,
                memory_gb,
                server.status.value,
                server.id,
                server.created_at.strftime("%Y-%m-%d %H:%M"),
            )
        )

    if not found_servers:
        click.echo("No servers.")
        return

    if format == "table":
        if project:
            found_servers = [server[1:] for server in found_servers]
            headers = headers[1:]
        click.echo(tabulate(found_servers, headers, tablefmt="plain"))

    elif format == "ssh-config":
        config_entries = []
        for server in found_servers:
            server_name = server[1]
            project_name = project if project else server[0]
            ssh_details = _get_ssh_details(project_name, server_name)
            host = f"{server_name}-{project_name.lower().replace(' ', '_')}"
            config_entries.append(
                f"""Host {host}
    HostName {ssh_details.hostname}
    User {ssh_details.username}
    Port {ssh_details.port}"""
            )

        click.echo("\n".join(config_entries))

    else:
        for server in found_servers:
            click.echo(server[1])


@server.command(name="open")
@click.argument("project")
@click.option("--server", is_flag=False, help="Name or ID of server to use.")
def open_(project, server):
    """Open a Faculty server in your browser."""
    project_id, server_id = _resolve_server(project, server)

    client = faculty.client("server")
    server = client.get(project_id, server_id)

    https_services = [
        service for service in server.services if service.name == "https"
    ]
    if not https_services:
        _print_and_exit(
            "Server {} is not running an application that "
            "can be opened in a web browser".format(server.name),
            1,
        )
    [https_service] = https_services
    url = "{}://{}".format(https_service.scheme, https_service.host)
    click.echo("Opening {}".format(url))
    click.launch(url)


@server.command()
@click.argument("project")
@click.option(
    "--cores",
    type=float,
    default=1,
    show_default=True,
    help="Number of CPU cores",
)
@click.option(
    "--memory",
    type=float,
    default=4,
    show_default=True,
    help="Server memory in GB",
)
@click.option(
    "--type",
    "type_",
    is_flag=False,
    default="jupyter",
    show_default=True,
    help="Server type",
)
@click.option(
    "--machine-type",
    "machine_type",
    default=None,
    show_default=False,
    help="Machine type for a dedicated instance, e.g. m5.xlarge. "
    "If set, the memory and CPU arguments are ignored.",
)
@click.option(
    "--version",
    "version",
    is_flag=False,
    help="Server image version [advanced]",
)
@click.option("--name", is_flag=False, help="Name to assign to the server")
@click.option(
    "--environment",
    "environments",
    multiple=True,
    help="Environments to apply to the server",
)
@click.option(
    "--wait",
    is_flag=True,
    help="Wait until the server is running before exiting.",
)
def new(
    project,
    cores,
    memory,
    type_,
    machine_type,
    version,
    name,
    environments,
    wait,
):
    """Create a new Faculty server."""
    # pylint: disable=too-many-arguments
    project_id = _resolve_project(project)
    environment_ids = [
        _resolve_environment(project_id, env) for env in environments
    ]

    if machine_type is None or machine_type == "custom":
        resources = SharedServerResources(
            milli_cpus=int(cores * 1000), memory_mb=int(memory * 1000)
        )

    elif machine_type is not None and machine_type != "custom":
        resources = DedicatedServerResources(node_type=machine_type)

    client = faculty.client("server")
    try:
        server_id = client.create(
            project_id, type_, resources, name, version, environment_ids
        )
    except faculty.clients.base.BadRequest as err:
        _print_and_exit(err.error, 64)

    server = client.get(project_id, server_id)
    click.echo("Creating server {} in project {}".format(server.name, project))
    if wait:
        while True:
            server_ids = {
                server_.id
                for server_ in _get_servers(
                    project_id, status=ServerStatus.RUNNING
                )
            }
            if server.id in server_ids:
                break
            time.sleep(1)


@server.command()
@click.argument("project")
@click.argument("server")
def terminate(project, server):
    """Terminate a Faculty server."""
    _, server_id = _resolve_server(project, server, ensure_running=False)
    client = faculty.client("server")
    client.delete(server_id)


@server.command(name="instance-types")
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Print extra information about instance types.",
)
def instance_types(verbose):
    """List the types of servers available on dedicated infrastructure."""
    client = faculty.client("cluster")
    types = client.list_single_tenanted_node_types(
        interactive_instances_configured=True
    )
    types = sorted(types, key=operator.attrgetter("cost_usd_per_hour"))

    if verbose:
        if not types:
            click.echo("No servers on dedicated infrastructure available.")

        else:
            headers = (
                "Machine Type",
                "CPUs",
                "RAM",
                "GPUs",
                "GPU Name",
                "Cost",
            )
            rows = [
                (
                    type_.name,
                    "{:.3g}".format(type_.milli_cpus / 1000),
                    "{:.3g} GB".format(type_.memory_mb / 1000),
                    type_.num_gpus or "-",
                    type_.gpu_name or "-",
                    "$ {:.3f} / hour".format(type_.cost_usd_per_hour),
                )
                for type_ in types
            ]
            click.echo(tabulate(rows, headers, tablefmt="plain"))

    else:
        for type_ in types:
            click.echo(type_.name)


@server.command()
@click.argument("project")
@click.argument("server")
def ssh_details(project, server):
    """Echo the username, hostname and SSH port for a Faculty server.

    After running this command, SSH into the server using:

    $ ssh <username>@<hostname> -p <port>

    For this command to work, you will first need to add your public SSH key
    to `~/.ssh/authorized_keys` on the Faculty Platform.

    """
    details = _get_ssh_details(project, server)
    click.echo(
        tabulate(
            [(details.hostname, details.port, details.username)],
            ("Hostname", "Port", "Username"),
            tablefmt="plain",
        )
    )


@cli.command(context_settings={"ignore_unknown_options": True})
@click.argument("project")
@click.argument("server")
@click.argument("ssh_opts", nargs=-1, type=click.UNPROCESSED)
def shell(project, server, ssh_opts):
    """Open a shell on a Faculty server.

    Any additional arguments given are passed on to SSH. This allows you to set
    up, for example, port forwarding:

    $ faculty shell <project> <server> -L 9000:localhost:8888

    """

    details = _get_ssh_details(project, server)

    with _save_key_to_file(details.key) as filename:
        cmd = (
            ["ssh"]
            + SSH_OPTIONS
            + [
                "-p",
                str(details.port),
                "-i",
                filename,
                "{}@{}".format(details.username, details.hostname),
            ]
        )
        cmd += list(ssh_opts)
        _run_ssh_cmd(cmd)


@cli.group()
def environment():
    """Manipulate Faculty server environments."""
    _check_credentials()


@environment.command(name="list")
@click.argument("project")
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Print extra information about environments.",
)
def list_environments(project, verbose):
    """List your environments."""
    client = faculty.client("environment")
    project_id = _resolve_project(project)
    environments = client.list(project_id)
    if verbose:
        if not environments:
            click.echo("No environments.")
        else:
            click.echo(
                tabulate(
                    [(e.name, e.id) for e in environments],
                    ("Environment Name", "ID"),
                    tablefmt="plain",
                )
            )
    else:
        for environment in environments:
            click.echo(environment.name)


@environment.command()
@click.argument("project")
@click.argument("server")
@click.argument("environment")
def apply(project, server, environment):
    """Apply an environment to the server."""
    project_id, server_id = _resolve_server(project, server)
    environment_id = _resolve_environment(project_id, environment)

    client = faculty.client("server")
    client.apply_environment(server_id, environment_id)

    click.echo(
        "Applying environment {} to server {} for project {}".format(
            environment, server, project
        )
    )


def _format_command(command):
    formatted_parts = []
    for part in command:
        if len(part.split()) > 1:
            formatted_parts.append(repr(part))
        else:
            formatted_parts.append(part)
    return " ".join(formatted_parts)


def _get_service(server, name):
    for service in server.services:
        if service.name == name:
            return service
    raise RuntimeError("cube has no service called {}".format(name))


def _get_hound_url(server):
    service = _get_service(server, "hound")
    return "{}://{}:{}".format(service.scheme, service.host, service.port)


@environment.command()
@click.argument("project")
@click.argument("server")
def status(project, server):
    """Get the execution status for an environment."""
    project_id, server_id = _resolve_server(project, server)

    server_client = faculty.client("server")
    server = server_client.get(project_id, server_id)

    hound_url = _get_hound_url(server)
    session = get_session()

    client = ServerAgentClient(hound_url, session)
    execution = client.latest_environment_execution()

    if execution is None:
        msg = "No environment has yet been applied to this server."
        _print_and_exit(msg, 64)

    click.echo("Latest environment execution:")
    click.echo("  Status: {}".format(execution.status.value))
    for i, environment in enumerate(execution.environments):
        click.echo("")
        click.echo("Environment {}".format(i))
        for j, step in enumerate(environment.steps):
            click.echo("")
            click.echo("Step {}:".format(j))
            click.echo("  Status:  {}".format(step.status.value))
            click.echo("  Command: {}".format(_format_command(step.command)))


@environment.command()
@click.argument("project")
@click.argument("server")
@click.option(
    "--step",
    "-s",
    "step_number",
    type=int,
    help="Display only the logs for this step",
)
def logs(project, server, step_number):
    """Stream the logs for a server environment application."""
    project_id, server_id = _resolve_server(project, server)

    server_client = faculty.client("server")
    server = server_client.get(project_id, server_id)

    hound_url = _get_hound_url(server)
    session = get_session()

    client = ServerAgentClient(hound_url, session)
    execution = client.latest_environment_execution()

    if execution is None:
        msg = "No environment has yet been applied to this server."
        _print_and_exit(msg, 64)

    steps = [
        step
        for environment_execution in execution.environments
        for step in environment_execution.steps
    ]

    if step_number is not None:
        try:
            steps = [steps[step_number]]
        except IndexError:
            _print_and_exit("step {} out of range".format(step_number), 64)

    for step in steps:
        for line in client.stream_environment_execution_step_logs(
            execution.id, step.id
        ):
            click.echo(line.content)


@cli.group()
def job():
    """Manipulate Faculty jobs."""
    pass


@job.command(name="list")
@click.argument("project")
@click.option(
    "-v", "--verbose", is_flag=True, help="Print extra information about jobs."
)
def list_jobs(project, verbose):
    """List the jobs in a project."""

    project_id = _resolve_project(project)

    client = faculty.client("job")
    jobs = client.list(project_id)
    if verbose:
        if not jobs:
            click.echo("No jobs.")
        else:
            rows = [
                (job.metadata.name, job.id, job.metadata.description)
                for job in jobs
            ]
            click.echo(
                tabulate(rows, ("Name", "ID", "Description"), tablefmt="plain")
            )
    else:
        for job in jobs:
            click.echo(job.metadata.name)


@job.command(name="list-runs")
@click.argument("project")
@click.argument("job")
@click.option(
    "-v", "--verbose", is_flag=True, help="Print extra information about runs."
)
def list_job_runs(project, job, verbose):
    """List the runs of a job."""

    project_id, job_id = _resolve_job(project, job)

    client = faculty.client("job")

    def list_runs():
        list_runs_result = client.list_runs(project_id, job_id)
        for run in list_runs_result.runs:
            yield run
        while list_runs_result.pagination.next is not None:
            list_runs_result = client.list_runs(
                project_id,
                job_id,
                start=list_runs_result.pagination.next.start,
                limit=list_runs_result.pagination.next.limit,
            )
            for run in list_runs_result.runs:
                yield run

    runs = list(list_runs())
    if verbose:
        if not runs:
            click.echo("No runs.")
        else:
            rows = [
                (
                    run.run_number,
                    run.id,
                    run.state.value,
                    _format_datetime(run.submitted_at),
                    _format_datetime(run.started_at),
                    _format_datetime(run.ended_at),
                )
                for run in runs
            ]
            click.echo(
                tabulate(
                    rows,
                    (
                        "Number",
                        "ID",
                        "State",
                        "Submitted At",
                        "Started At",
                        "Ended At",
                    ),
                    tablefmt="plain",
                )
            )
    else:
        for run in runs:
            click.echo(run.run_number)


@job.command(name="run")
@click.argument("project")
@click.argument("job")
@click.argument(
    "parameter_values",
    type=faculty_cli.parse.parse_parameter_values,
    nargs=-1,
    required=False,
)
@click.option("--num-subruns", type=int, help="Number of sub runs")
def run_job(project, job, parameter_values, num_subruns):
    """Run a job.

    \b
    To run a single job:
    $ faculty job run PROJECT JOB

    \b
    To run a single job with parameters:
    $ faculty job run PROJECT JOB "foo=bar,eggs=spam"

    \b
    To run a job multiple times with different parameters:
    $ faculty job run PROJECT JOB "foo=bar,eggs=spam" "foo=bar2,eggs=spam2"

    \b
    To run a job multiple times with no parameters:
    $ faculty job run PROJECT JOB --num-subruns 2

    """

    if num_subruns is None and not parameter_values:
        parameter_values = [{}]
    elif num_subruns is None and parameter_values:
        pass
    elif num_subruns is not None and not parameter_values:
        parameter_values = [{} for _ in range(num_subruns)]
    else:
        _print_and_exit(
            "Cannot set both 'parameter_values' and 'num_subruns'.", 64
        )

    project_id, job_id = _resolve_job(project, job)

    client = faculty.client("job")
    client.create_run(project_id, job_id, parameter_values)

    if len(parameter_values) == 1:
        run_type = "run"
        suffix = ""
    else:
        run_type = "run array"
        suffix = " with {} subruns".format(len(parameter_values))

    click.echo(
        "Submitted {} of job '{}' in project '{}'{}".format(
            run_type, job, project, suffix
        )
    )


@job.command("logs")
@click.argument("project")
@click.argument("job")
@click.argument("run", type=faculty_cli.parse.parse_run_identifier)
def job_run_logs(project, job, run):
    """Print the logs for a run."""

    project_id, job_id = _resolve_job(project, job)

    job_client = faculty.client("job")
    run_details = job_client.get_run(project_id, job_id, run.run_number)
    if run.subrun_number is not None:
        subrun_number = run.subrun_number
    elif len(run_details.subruns) == 1:
        subrun_number = run_details.subruns[0].subrun_number
    else:
        _print_and_exit(
            (
                "Run {0} has {1} subruns. You must specify the subrun "
                "to show logs from, e.g. '{0}.1'."
            ).format(run.run_number, len(run_details.subruns)),
            64,
        )

    subrun_details = job_client.get_subrun(
        project_id, job_id, run.run_number, subrun_number
    )

    log_client = faculty.client("log")

    for env_step_exec in subrun_details.environment_step_executions:
        env_name = env_step_exec.environment_name
        click.secho(
            'Logs for step of environment "{}":'.format(env_name), fg="yellow"
        )
        parts = log_client.get_subrun_environment_step_logs(
            project_id,
            job_id,
            run_details.id,
            subrun_details.id,
            env_step_exec.environment_step_id,
        )
        click.echo("".join(part.content for part in parts), nl=False)

    click.secho("Logs for job command:", fg="yellow")
    parts = log_client.get_subrun_command_logs(
        project_id, job_id, run_details.id, subrun_details.id
    )
    click.echo("".join(part.content for part in parts), nl=False)


@cli.group()
def file():
    """Manipulate files in a Faculty project."""
    _check_credentials()


@file.command()
@click.argument("project")
@click.argument("local")
@click.argument("remote")
@click.option("--server", is_flag=False, help="Name or ID of server to use.")
def put(project, local, remote, server):
    """Copy a local file to Faculty workspace."""

    project_id, server_id = _resolve_server(project, server)

    client = faculty.client("server")
    details = client.get_ssh_details(project_id, server_id)

    escaped_remote = faculty_cli.shell.quote(remote)

    with _save_key_to_file(details.key) as filename:
        cmd = (
            ["scp"]
            + SSH_OPTIONS
            + [
                "-i",
                filename,
                "-P",
                str(details.port),
                os.path.expanduser(local),
                "{}@{}:{}".format(
                    details.username, details.hostname, escaped_remote
                ),
            ]
        )
        _run_ssh_cmd(cmd)


@file.command()
@click.argument("project")
@click.argument("remote")
@click.argument("local")
@click.option("--server", is_flag=False, help="Name or ID of server to use.")
def get(project, remote, local, server):
    """Copy a file from Faculty workspace to the local machine."""

    project_id, server_id = _resolve_server(project, server)

    client = faculty.client("server")
    details = client.get_ssh_details(project_id, server_id)

    escaped_remote = faculty_cli.shell.quote(remote)

    with _save_key_to_file(details.key) as filename:
        cmd = (
            ["scp"]
            + SSH_OPTIONS
            + [
                "-i",
                filename,
                "-P",
                str(details.port),
                "{}@{}:{}".format(
                    details.username, details.hostname, escaped_remote
                ),
                os.path.expanduser(local),
            ]
        )
        _run_ssh_cmd(cmd)


def _rsync(project, local, remote, server, rsync_opts, up):
    """Sync files from or to server."""

    project_id, server_id = _resolve_server(project, server)

    client = faculty.client("server")
    details = client.get_ssh_details(project_id, server_id)

    escaped_remote = faculty_cli.shell.quote(remote)
    if up:
        path_from = local
        path_to = "{}@{}:{}".format(
            details.username, details.hostname, escaped_remote
        )
    else:
        path_from = "{}@{}:{}".format(
            details.username, details.hostname, escaped_remote
        )
        path_to = local

    with _save_key_to_file(details.key) as filename:
        ssh_cmd = "ssh {} -p {} -i {}".format(
            " ".join(SSH_OPTIONS), details.port, filename
        )

        rsync_cmd = ["rsync", "-a", "-e", ssh_cmd, path_from, path_to]
        rsync_cmd += list(rsync_opts)

        _run_ssh_cmd(rsync_cmd)


@file.command(
    name="sync-up", context_settings={"ignore_unknown_options": True}
)
@click.argument("project")
@click.argument("local")
@click.argument("remote")
@click.argument("rsync_opts", nargs=-1, type=click.UNPROCESSED)
@click.option("--server", is_flag=False, help="Name or ID of server to use.")
def sync_up(project, local, remote, server, rsync_opts):
    """Sync local files up to a project with rsync.

    Arguments are used as "rsync -a LOCAL server:REMOTE [RSYNC_OPTS]".

    """
    _rsync(project, local, remote, server, rsync_opts, True)


@file.command(
    name="sync-down", context_settings={"ignore_unknown_options": True}
)
@click.argument("project")
@click.argument("remote")
@click.argument("local")
@click.argument("rsync_opts", nargs=-1, type=click.UNPROCESSED)
@click.option("--server", is_flag=False, help="Name or ID of server to use.")
def sync_down(project, remote, local, server, rsync_opts):
    """Sync remote files down from project with rsync.

    Arguments are used as "rsync -a server:REMOTE LOCAL [RSYNC_OPTS]".

    """
    _rsync(project, local, remote, server, rsync_opts, False)


@file.command()
@click.argument("project")
@click.argument("path")
def ls(project, path):
    """List files and directories on Faculty workspace."""
    if not path.startswith("/project"):
        _print_and_exit("{} is outside the project workspace".format(path), 66)

    project_id = _resolve_project(project)
    relative_path = os.path.relpath(path, "/project")
    client = faculty.client("workspace")

    try:
        directory_details_list = client.list(
            project_id=project_id, prefix=relative_path, depth=1
        )
    except faculty.clients.base.NotFound:
        _print_and_exit("{}: No such file or directory".format(path), 66)

    try:
        [directory_details] = directory_details_list
    except ValueError:
        _print_and_exit("Zero or more than one objects returned", 70)

    for item in directory_details.content:
        if hasattr(item, "content"):
            click.echo("/project{}/".format(item.path))
        else:
            click.echo("/project{}".format(item.path))


@cli.group()
def datasets():
    """Manipulate files in Faculty datasets."""
    pass


@datasets.command(name="get")
@click.argument("project")
@click.argument("project_path")
@click.argument("local_path")
def dataset_get(project, project_path, local_path):
    """Copy from a project's datasets to the local filesystem."""
    project_id = _resolve_project(project)
    try:
        faculty.datasets.get(project_path, local_path, project_id=project_id)
    except faculty.datasets.util.DatasetsError as err:
        _print_and_exit(str(err).replace(str(project_id), project), 64)
    except OSError as err:
        _print_and_exit(err, 64)


@datasets.command(name="put")
@click.argument("project")
@click.argument("local_path")
@click.argument("project_path")
def dataset_put(project, local_path, project_path):
    """Copy from the local filesystem to a project's datasets."""
    project_id = _resolve_project(project)
    try:
        faculty.datasets.put(local_path, project_path, project_id=project_id)
    except (faculty.clients.object.PathAlreadyExists, OSError) as err:
        _print_and_exit(err, 64)


@datasets.command()
@click.argument("project")
@click.argument("source_path")
@click.argument("destination_path")
def mv(project, source_path, destination_path):
    """Move a file within a project's datasets."""
    project_id = _resolve_project(project)
    try:
        faculty.datasets.mv(
            source_path, destination_path, project_id=project_id
        )
    except faculty.clients.object.PathNotFound as err:
        _print_and_exit(err, 64)


@datasets.command()
@click.argument("project")
@click.argument("source_path")
@click.argument("destination_path")
@click.option(
    "--recursive",
    is_flag=True,
    help="Copy directories like a recursive copy in a filesystem",
)
def cp(project, source_path, destination_path, recursive):
    """Copy a file within a project's datasets."""
    project_id = _resolve_project(project)
    try:
        faculty.datasets.cp(
            source_path,
            destination_path,
            project_id=project_id,
            recursive=recursive,
        )
    except (
        faculty.clients.object.PathNotFound,
        faculty.clients.object.SourceIsADirectory,
    ) as err:
        _print_and_exit(err, 64)


@datasets.command()
@click.argument("project")
@click.argument("project_path")
@click.option(
    "--recursive",
    is_flag=True,
    help="Deleting directories like a recursive delete in a filesystem",
)
def rm(project, project_path, recursive):
    """Remove a file from the project's datasets."""
    project_id = _resolve_project(project)
    try:
        faculty.datasets.rm(
            project_path, project_id=project_id, recursive=recursive
        )
    except (
        faculty.clients.object.PathNotFound,
        faculty.clients.object.TargetIsADirectory,
    ) as err:
        _print_and_exit(err, 64)


@datasets.command(name="ls")
@click.argument("project")
@click.option(
    "--prefix",
    default="/",
    help="List only files in the datasets matching this prefix.",
)
@click.option(
    "--show-hidden", is_flag=True, help="Include hidden files in the output."
)
def dataset_ls(project, prefix, show_hidden):
    """List contents of project datasets."""
    project_id = _resolve_project(project)
    for item in faculty.datasets.ls(
        prefix, project_id=project_id, show_hidden=show_hidden
    ):
        click.echo(item)
