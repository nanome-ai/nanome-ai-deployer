import enums
import getpass
import os
from cli import utils, mara

PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), 'playbooks')


def setup_mara(host=None, protocol='', certs_path=''):
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
        host = input('What Domain name will you be using for this server? (ex. yourcompany.com) (Defaults to ip address) ')
        if not host:
            host = utils.get_public_ip() + '.nip.io'

    # Gather https info if not provided.
    if not protocol:
        https_info = utils.gather_https_info()
        protocol = 'https' if https_info['https_enabled'] else 'http'
        certs_path = https_info.get('certs_path', '')

    # Set SSL cert paths
    use_https = protocol == 'https'
    ssl_cert_path = ssl_key_path = ''
    if certs_path:
        ssl_cert_path = f'{certs_path}/certs.pem'
        ssl_key_path = f'{certs_path}/key.pem'

    # Setup tool-server .env file
    print("\nCollecting Tool Server Values...\n")
    tool_server_host = f'mara-tools.{host}'
    tool_server_env_file = enums.TOOL_SERVER_ENV_FILE
    existing_tool_server_env = utils.read_env_file(tool_server_env_file)
    tool_server_env = mara.configure_tool_server(existing_tool_server_env)
    tool_server_env.update(
        HTTPS=use_https,
        FILES_VOLUME='nanome-ai-deployer_mara-tool-volume',
        VIRTUAL_HOST=tool_server_host,
    )
    if certs_path:
        tool_server_env.update(
            SSL_CERT_PATH=ssl_cert_path,
            SSL_KEY_PATH=ssl_key_path,
        )
    utils.write_env_file(tool_server_env_file, tool_server_env)

    # Configure the mara .env file
    tool_server_api_key = tool_server_env.get('API_KEY', None)
    print('\nConfiguring the MARA Server...\n')
    mara_host = f'mara.{host}'
    mara_env_file = enums.MARA_ENV_FILE
    existing_mara_env = utils.read_env_file(mara_env_file)
    mara_env = mara.configure_mara_server(existing_mara_env)

    mara_env.update(
        HTTPS=use_https,
        API_HOST=mara_host,
        TOOL_SERVER_KEY=tool_server_api_key,
        TOOL_SERVER_URL=f'{protocol}://{tool_server_host}',
        VIRTUAL_HOST=mara_host,
    )
    if certs_path:
        mara_env.update(
            SSL_CERT_PATH=ssl_cert_path,
            SSL_KEY_PATH=ssl_key_path,
        )

    utils.write_env_file(mara_env_file, mara_env)
    return mara_env, tool_server_env


if __name__ == "__main__":
    mara_env, tool_server_env = setup_mara()
    mara_host = mara_env['VIRTUAL_HOST']
    tool_server_host = tool_server_env['VIRTUAL_HOST']
    print(
        "\nYour Services have been configured to run at the following urls\n"
        f"\t- MARA: {mara_host}\n"
        f"\t- MARA Tool Server: {tool_server_host}\n"
        "\n To start the services, run `docker compose up -d`"
    )
