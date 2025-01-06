import getpass
import os
from cli import utils, mara, workspace
import enums

PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), 'playbooks')


def main():
    print(
        "\nThanks for using Nanome AI! Let's get started setting up your server!\n"
        "This script will download and run 4 docker containers:\n"
        "\t- Workspace API: Acts as a data store of Nanome workspaces.\n"
        "\t- Workspace Load Service: Contains business logic for rendering structure files as a Nanome workspace.\n"
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

    print("Deploying Workspace API...")
    workspace.configure_workspace_api(inventory_filepath)
    
    print("Deploying Workspace Load Service...")
    workspace.configure_workspace_load_service(inventory_filepath)

    # Setup tool-server deployment
    print("\nCollecting Tool Server Values...\n")
    tool_server_env_file = enums.TOOL_SERVER_ENV_FILE
    existing_tool_server_env = utils.read_env_file(tool_server_env_file)
    tool_server_api_key = existing_tool_server_env.get('API_KEY', None)

    tool_server_env = mara.configure_tool_server(existing_tool_server_env)
    with open(tool_server_env_file, 'w') as f:
        for key, value in tool_server_env.items():
            line = f'{key}={value}\n'
            f.write(line)
    
    # Configure the mara deployment
    print('\nConfiguring the MARA Server...\n')
    mara_env_file = enums.MARA_ENV_FILE
    existing_mara_env = utils.read_env_file(mara_env_file)
    mara_env = mara.configure_mara_server(existing_mara_env, tool_server_api_key)
    mara_env['TOOL_SERVER_KEY'] = tool_server_api_key
    with open(mara_env_file, 'w') as f:
        for key, value in mara_env.items():
            line = f'{key}={value}\n'
            f.write(line)

    print(
        "\nYour Services have been set up\n"
        "\t- MARA: 127.0.0.1:8000\n"
        "\t- Tool Server: 127.0.0.1:8001\n"
        "\t- Workspace API: 127.0.0.1:8002\n"
        "\t- Workspace Load Service: 127.0.0.1:8003\n"
    )

if __name__ == "__main__":
    main()
