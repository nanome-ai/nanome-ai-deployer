import enums
import getpass
import os
from cli import utils, mara

PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), 'playbooks')
EMBEDDINGS_VOLUME = 'nanome-ai-deployer_mara-embeddings-volume'


def _write_compose_env(mara_env):
    """Manage the root .env that ``docker compose`` reads.

    Toggles the ``local-embeddings`` profile (which gates the bundled
    ``mara-hf-tei`` service) and forwards the chosen HF model id so the
    TEI container loads the same one mara-ai will query. The marker is
    ``EMBEDDING_API_URL`` — only the local-embeddings branch sets it.
    """
    compose_env = utils.read_env_file(enums.COMPOSE_ENV_FILE)
    uses_local_embeddings = (mara_env.get('EMBEDDING_API_URL') or '').startswith(
        'http://mara-hf-tei'
    )
    if uses_local_embeddings:
        compose_env['COMPOSE_PROFILES'] = 'local-embeddings'
        compose_env['TEI_MODEL_ID'] = mara_env.get('EMBEDDING_MODEL', '')
    else:
        compose_env.pop('COMPOSE_PROFILES', None)
        compose_env.pop('TEI_MODEL_ID', None)
    utils.write_env_file(enums.COMPOSE_ENV_FILE, compose_env)


def _warn_if_embedding_model_changed(old, new):
    """Chroma persists vectors in a model-specific space and dimensionality.
    Switching ``EMBEDDING_MODEL`` makes existing vectors incompatible, the
    operator must drop the volume before bringing the stack back up.
    """
    if not old or not new or old == new:
        return
    print(
        f"\n!! EMBEDDING_MODEL changed: {old} -> {new}\n"
        "   Persisted embedding vectors are incompatible with the new model.\n"
        "   Before `docker compose up -d`, run:\n"
        "     docker compose down\n"
        f"     docker volume rm {EMBEDDINGS_VOLUME}\n"
    )


def setup_mara(host=None, cert_type=''):
    if not host:
        # If host is provided, then the user already got a welcome message
        print(
            "\nThanks for using MARA! Let's get started setting up your server!\n\n"
            "This script will download and run 3 docker containers:\n"
            " - MARA: Web Application and API for performing comp-chem workflows.\n"
            " - MARA Tool Server: Runs computations for MARA workflows.\n"
            " - MARA Embeddings: Vector database for storing embeddings.\n"
        )
        input('Press ENTER to continue')

    if not host:
        # Check existing env files for a default host
        existing_mara_env = utils.read_env_file(enums.MARA_ENV_FILE)
        default_host = utils.extract_host_from_env(existing_mara_env, 'nanome')
        host = utils.gather_host_info(default=default_host)

    # Gather https info if not provided.
    if not cert_type:
        cert_type = utils.gather_https_info(host)
    protocol = 'http' if cert_type == 'None' else 'https'

    # Setup tool-server .env file
    tool_server_host = f'nanome-tools.{host}'
    tool_server_env_file = enums.TOOL_SERVER_ENV_FILE
    existing_tool_server_env = utils.read_env_file(tool_server_env_file)
    tool_server_env = mara.configure_tool_server(existing_tool_server_env)
    tool_server_env.update(
        FILES_VOLUME='nanome-ai-deployer_mara-tool-volume',
        VIRTUAL_HOST=tool_server_host,
    )
    if cert_type == 'Default':
        tool_server_env.update(
            CERT_NAME='default',
            REQUESTS_CA_BUNDLE='/certs/bundle.pem',
        )
    elif cert_type == 'Individual':
        tool_server_env.update(
            CERT_NAME='nanome-tools',
            REQUESTS_CA_BUNDLE='/certs/bundle.pem',
        )
    else:
        tool_server_env.pop('CERT_NAME', None)
        tool_server_env.pop('REQUESTS_CA_BUNDLE', None)
    utils.write_env_file(tool_server_env_file, tool_server_env)

    # Configure the mara .env file
    tool_server_api_key = tool_server_env.get('API_KEY', None)
    mara_host = f'nanome.{host}'
    existing_mara_env = utils.read_env_file(enums.MARA_ENV_FILE)
    mara_env = mara.configure_mara_server(existing_mara_env)

    _warn_if_embedding_model_changed(
        old=existing_mara_env.get('EMBEDDING_MODEL'),
        new=mara_env.get('EMBEDDING_MODEL'),
    )

    mara_env.update(
        API_HOST=mara_host,
        TOOL_SERVER_KEY=tool_server_api_key,
        TOOL_SERVER_URL=f'{protocol}://{tool_server_host}',
        VIRTUAL_HOST=mara_host,
    )
    if cert_type == 'Default':
        mara_env.update(
            CERT_NAME='default',
            REQUESTS_CA_BUNDLE='/certs/bundle.pem',
        )
    elif cert_type == 'Individual':
        mara_env.update(
            CERT_NAME='nanome',
            REQUESTS_CA_BUNDLE='/certs/bundle.pem',
        )
    else:
        mara_env.pop('CERT_NAME', None)
        mara_env.pop('REQUESTS_CA_BUNDLE', None)

    utils.write_env_file(enums.MARA_ENV_FILE, mara_env)
    _write_compose_env(mara_env)
    return mara_env, tool_server_env


if __name__ == "__main__":
    try:
        mara_env, tool_server_env = setup_mara()
        mara_host = mara_env['VIRTUAL_HOST']
        tool_server_host = tool_server_env['VIRTUAL_HOST']
        print(
            "\nYour services have been configured to run at the following urls\n"
            f" - Web UI: {mara_host}\n"
            f" - Tool Server: {tool_server_host}\n"
            "\nTo start the services, run `docker compose up -d`"
        )
    except KeyboardInterrupt:
        print("\nSetup cancelled")
