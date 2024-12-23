import getpass
import os
from cli.utils import gather_https_info, create_inventory_file
from cli.mara import configure_mara_server, configure_tool_server
from cli.workspace import configure_workspace_api, configure_workspace_load_service


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
    mara_host_config = gather_https_info()
    if not os.path.exists(inventory_filepath):
        mara_host_config.update({
            'ansible_host': '127.0.0.1',
            'ansible_user': getpass.getuser(),
            'ansible_connection': 'local'
        })
        create_inventory_file(inventory_filepath, mara_host_config)

    print("Deploying Workspace API...")
    configure_workspace_api(inventory_filepath)
    
    print("Deploying Workspace Load Service...")
    configure_workspace_load_service(inventory_filepath)

    # Setup tool-server deployment
    api_key_file = os.path.join(os.path.dirname(__file__), 'tool_server_api_key.txt')
    print("Deploying the Tool Server...")
    configure_tool_server(inventory_filepath, api_key_file)

    # Configure the mara deployment
    print('\nDeploying the MARA Server...\n')
    with open(api_key_file, 'r') as f:
        tool_server_api_key = f.read()
    configure_mara_server(inventory_filepath, tool_server_api_key)
    os.remove(api_key_file)

    print(
        "\nYour Services have been set up\n"
        "\t- MARA: 127.0.0.1:8000\n"
        "\t- Tool Server: 127.0.0.1:8001\n"
        "\t- Workspace API: 127.0.0.1:8002\n"
        "\t- Workspace Load Service: 127.0.0.1:8003\n"
    )

if __name__ == "__main__":
    main()
