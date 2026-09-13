"""Generate a persistent local database password without storing it in source or logs."""

import os
import secrets
from pathlib import Path

target = Path("/run/signalrank/db_password")
if not target.exists():
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o444)
    with os.fdopen(descriptor, "w") as output:
        output.write(secrets.token_urlsafe(48))
print("Local database credential is ready.")
