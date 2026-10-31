import os
import sys

from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.environ.get("DB_HOST")
DB_PORT = int(os.environ.get("DB_PORT", "3306"))
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_NAME = os.environ.get("DB_NAME")

ENV = os.environ.get("ENV", "development")
IS_PRODUCTION = ENV == "production"
PORT = int(os.environ.get("PORT", "8000"))

# Fail fast on missing config, before any DB/network work starts. This app
# gets copied and re-deployed repeatedly across different domains/projects
# (see the build-fullstack-python-angular-app skill) - a clear startup
# error here saves a debugging session every time someone forgets to set
# up .env on a fresh clone, instead of letting it surface as an opaque
# mysql-connector error three layers down.
_required = {
    "DB_HOST": DB_HOST,
    "DB_USER": DB_USER,
    "DB_PASSWORD": DB_PASSWORD,
    "DB_NAME": DB_NAME,
}
_missing = [name for name, value in _required.items() if not value]
if _missing:
    print(
        f"Missing required environment variable(s): {', '.join(_missing)}. "
        "Create a MySQL database and put its connection details in a .env "
        "file (see .env.example).",
        file=sys.stderr,
    )
    sys.exit(1)
