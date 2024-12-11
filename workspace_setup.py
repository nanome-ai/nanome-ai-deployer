import os
import subprocess

PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), 'playbooks')


def main():
    print((
        "\nLets get your workspace apis set up.\n\n"
        "This script will do 2 things:\n"
        "\t- Run the Workspace API.\n"
        "\t- Run the Workspace Load Service.\n"
        
    ))

    inventory_filepath = os.path.join(os.path.dirname(__file__), 'inventory.local.yaml')
    if not os.path.exists(inventory_filepath):
        raise Exception(f"Inventory file not found: {inventory_filepath}")

    print("Deploy Workspace API...")
    deploy_workspace_api_playbook = os.path.join(PLAYBOOKS_DIR, 'deploy_workspace_api.yaml')
    subprocess.run([
        'ansible-playbook',
        '-i', inventory_filepath,
        deploy_workspace_api_playbook
    ])

    print("Deploy Workspace Load Service...")
    deploy_workspace_load_service_playbook = os.path.join(PLAYBOOKS_DIR, 'deploy_workspace_load_service.yaml')
    subprocess.run([
        'ansible-playbook',
        '-i', inventory_filepath,
        deploy_workspace_load_service_playbook
    ])


if __name__ == "__main__":
    main()
