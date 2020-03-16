import uuid
import datetime

from faculty.clients.project import Project
from faculty.clients.server import (
    DedicatedServerResources,
    ServerStatus,
    SharedServerResources,
    Server,
    Service,
)
from faculty.config import Profile


USER_ID = uuid.uuid4()
PROJECT = Project(id=uuid.uuid4(), name="test-project", owner_id=USER_ID)

PROFILE = Profile(
    domain="services.subdomain.my.faculty.ai",
    protocol="https",
    client_id=uuid.uuid4(),
    client_secret="29o9P0q3BZiUDMx4R38haZCOPbuy3p7fGARUBD0a",
)

SERVER_CREATION_DATE = datetime.datetime(year=2020, month=1, day=1)
SERVICE = Service(
    name="test-service",
    host="test-host",
    port=8000,
    scheme="test-scheme",
    uri="test-uri",
)

DEDICATED_RESOURCE = DedicatedServerResources(node_type="m4.xlarge")
SHARED_RESOURCE = SharedServerResources(milli_cpus=1000, memory_mb=4000)
SHARED_SERVER = Server(
    id=uuid.uuid4(),
    project_id=PROJECT.id,
    owner_id=uuid.uuid4(),
    name="test-server",
    type="test-type",
    resources=SHARED_RESOURCE,
    created_at=SERVER_CREATION_DATE,
    status=ServerStatus.RUNNING,
    services=[SERVICE],
)
DEDICATED_SERVER = Server(
    id=uuid.uuid4(),
    project_id=PROJECT.id,
    owner_id=uuid.uuid4(),
    name="test-server",
    type="test-type",
    resources=DEDICATED_RESOURCE,
    created_at=SERVER_CREATION_DATE,
    status=ServerStatus.RUNNING,
    services=[SERVICE],
)
