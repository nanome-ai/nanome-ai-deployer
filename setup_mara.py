import enums
import getpass
import os
from cli import utils, mara

PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), 'playbooks')


def setup_mara(host=None):

    if not host:
        # If host is provided, then the user already got a welcome message
        print(
            "\nThanks for using MARA! Let's get started setting up your server!\n"
            "This script will download and run 2 docker containers:\n"
            "\t- Tool Server: Runs computations for MARA workflows.\n"
            "\t- MARA: Web Application and API for performing comp-chem workflows.\n"
        )
        input('Press ENTER to continue')

    if not host:
        host = input('What Domain name will you be using for this server? (ex. yourcompany.com) (Defaults to ip address ')
        if not host:
            host = utils.get_public_ip()

    # Setup tool-server .env file
    print("\nCollecting Tool Server Values...\n")
    tool_server_host = f'mara-tools.{host}'
    tool_server_env_file = enums.TOOL_SERVER_ENV_FILE
    existing_tool_server_env = utils.read_env_file(tool_server_env_file)
    tool_server_env = mara.configure_tool_server(existing_tool_server_env)
    tool_server_env['VIRTUAL_HOST'] = tool_server_host
    utils.write_env_file(tool_server_env_file, tool_server_env)

    # Configure the mara .env file
    tool_server_api_key = tool_server_env.get('API_KEY', None)
    print('\nConfiguring the MARA Server...\n')
    mara_env_file = enums.MARA_ENV_FILE
    existing_mara_env = utils.read_env_file(mara_env_file)
    mara_env = mara.configure_mara_server(existing_mara_env, tool_server_api_key)
    mara_env['TOOL_SERVER_KEY'] = tool_server_api_key
    mara_host = f'mara.{host}'
    mara_env['VIRTUAL_HOST'] = mara_host
    utils.write_env_file(mara_env_file, mara_env)
    return mara_env, tool_server_env


if __name__ == "__main__":
    mara_env, tool_server_env = setup_mara()
    mara_host = mara_env['VIRTUAL_HOST']
    tool_server_host = tool_server_env['VIRTUAL_HOST']
    print(
        "\nYour Services have been configured to run at the following urls\n"
        f"\t- MARA: {mara_host}\n"
        f"\t- Tool Server: {tool_server_host}\n"
        "\n To start the services, run `docker compose up -d"
    )