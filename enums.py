import os

MARA_ENV_FILE = os.path.join(os.path.dirname(__file__), '.env.maraserver')
TOOL_SERVER_ENV_FILE = os.path.join(os.path.dirname(__file__), '.env.toolserver')
WORKSPACES_ENV_FILE = os.path.join(os.path.dirname(__file__), '.env.workspaces')
AUTH_PROXY_ENV_FILE = os.path.join(os.path.dirname(__file__), '.env.auth_proxy')
# Root .env read by `docker compose` itself (not by any service) for variable
# substitution and COMPOSE_PROFILES gating of optional services.
COMPOSE_ENV_FILE = os.path.join(os.path.dirname(__file__), '.env')
