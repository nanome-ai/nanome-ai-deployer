import getpass
import os
from cli import utils, workspace

PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), 'playbooks')


def main():
    print(
        "\nThanks for using NanomeAI! Let's get started setting up your server!\n"
        "This script will download and run 2 docker containers:\n"
        "\t- Workspace API.\n"
        "\t- Workspace Load Service.\n"
    )
    input('Press ENTER to continue')
    inventory_filepath = os.path.join(os.path.dirname(__file__), 'inventory.local.yaml')
    host_config = utils.gather_https_info()
    if not os.path.exists(inventory_filepath):
        host_config.update({
            'ansible_host': '127.0.0.1',
            'ansible_user': getpass.getuser(),
            'ansible_connection': 'local'
        })
        utils.create_inventory_file(inventory_filepath, host_config)

    print("Deploying Workspace API...")
    workspace.configure_workspace_api(inventory_filepath)
    
    print("Deploying Workspace Load Service...")
    workspace.configure_workspace_load_service(inventory_filepath)

    print(
        "\nYour Services have been set up\n"
        "\t- Workspace API: 127.0.0.1:8002\n"
        "\t- Workspace Load Service: 127.0.0.1:8003\n"
    )

if __name__ == "__main__":
    main()
