import getpass
import os
from cli import utils, mara

PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), 'playbooks')


def main():
    print(
        "\nThanks for using MARA! Let's get started setting up your server!\n"
        "This script will download and run 2 docker containers:\n"
        "\t- Tool Server: Runs computations for MARA workflows.\n"
        "\t- MARA: Web Application and API for performing comp-chem workflows.\n"
    )
    input('Press ENTER to continue')

    inventory_filepath = os.path.join(os.path.dirname(__file__), 'inventory.local.yaml')
    mara_host_config = utils.gather_https_info()
    if not os.path.exists(inventory_filepath):
        mara_host_config.update({
            'ansible_host': '127.0.0.1',
            'ansible_user': getpass.getuser(),
            'ansible_connection': 'local'
        })
        utils.create_inventory_file(inventory_filepath, mara_host_config)

    # Setup tool-server deployment
    print("Collecting Tool Server Values...")
    tool_server_env_file = os.path.join(os.path.dirname(__file__), '.env.toolserver')
    existing_tool_server_env = utils.read_env_file(tool_server_env_file)
    tool_server_env = mara.configure_tool_server(inventory_filepath, existing_tool_server_env)
    with open(tool_server_env_file, 'w') as f:
        for key, value in tool_server_env.items():
            line = f'{key}={value}'
            f.write(line)
    tool_server_api_key = tool_server_env['API_KEY']
    # Configure the mara deployment

    print('\nConfiguring the MARA Server...\n')
    mara_env_file = os.path.join(os.path.dirname(__file__), '.env.maraserver')
    mara_env = mara.configure_mara_server(inventory_filepath, tool_server_api_key)
    mara_env['TOOL_SERVER_KEY'] = tool_server_api_key

    with open(mara_env_file, 'w') as f:
        for key, value in mara_env.items():
            line = f'{key}={value}'
            f.write(line)
    print(
        "\nYour Services have been set up\n"
        "\t- MARA: 127.0.0.1:8000\n"
        "\t- Tool Server: 127.0.0.1:8001\n"
    )

if __name__ == "__main__":
    main()
