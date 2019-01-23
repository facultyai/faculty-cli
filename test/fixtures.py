import uuid

from faculty.clients.project import Project
from faculty.config import Profile


USER_ID = uuid.uuid4()
PROJECT = Project(id=uuid.uuid4(), name="test-project", owner_id=USER_ID)

PROFILE = Profile(
    domain="services.subdomain.my.faculty.ai",
    protocol="https",
    client_id=uuid.uuid4(),
    client_secret="29o9P0q3BZiUDMx4R38haZCOPbuy3p7fGARUBD0a",
)
