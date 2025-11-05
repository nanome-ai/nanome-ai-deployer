import enums
import getpass
import os
from cli import utils, mara

PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), 'playbooks')


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
        host = input('\nWhat Domain name will you be using for this server? (ex. yourcompany.com) (Defaults to ip address) ')
        if not host:
            host = utils.get_public_ip() + '.nip.io'

    # Gather https info if not provided.
    if not cert_type:
        cert_type = utils.gather_https_info(host)
    protocol = 'http' if cert_type == 'None' else 'https'

    # Setup tool-server .env file
    tool_server_host = f'mara-tools.{host}'
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
            CERT_NAME='mara-tools',
            REQUESTS_CA_BUNDLE='/certs/bundle.pem',
        )
    else:
        tool_server_env.pop('CERT_NAME', None)
        tool_server_env.pop('REQUESTS_CA_BUNDLE', None)
    utils.write_env_file(tool_server_env_file, tool_server_env)

    # Configure the mara .env file
    tool_server_api_key = tool_server_env.get('API_KEY', None)
    mara_host = f'mara.{host}'
    existing_mara_env = utils.read_env_file(enums.MARA_ENV_FILE)
    mara_env = mara.configure_mara_server(existing_mara_env)

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
            CERT_NAME='mara',
            REQUESTS_CA_BUNDLE='/certs/bundle.pem',
        )
    else:
        mara_env.pop('CERT_NAME', None)
        mara_env.pop('REQUESTS_CA_BUNDLE', None)

    utils.write_env_file(enums.MARA_ENV_FILE, mara_env)
    return mara_env, tool_server_env


if __name__ == "__main__":
    try:
        mara_env, tool_server_env = setup_mara()
        mara_host = mara_env['VIRTUAL_HOST']
        tool_server_host = tool_server_env['VIRTUAL_HOST']
        print(
            "\nYour Services have been configured to run at the following urls\n"
            f"\t- MARA: {mara_host}\n"
            f"\t- MARA Tool Server: {tool_server_host}\n"
            "\nTo start the services, run `docker compose up -d`"
        )
    except KeyboardInterrupt:
        print("\nSetup cancelled")
