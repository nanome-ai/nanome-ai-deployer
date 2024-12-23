import getpass
import json
import os
import random
import string
import subprocess
import tempfile
import yaml

import cli
from cli.utils import PLAYBOOKS_DIR
from cli.mara import retrieve_aws_credentials_from_toolserver


def create_inventory_file(inventory_file, mara_host_config):
    # Construct the inventory structure
    inventory = {
        'myhosts': {
            'hosts': {
                'mara-servers': mara_host_config,
            }
        }
    }

    # Define the path to save the inventory file
    # Write the YAML structure to the file
    with open(inventory_file, 'w') as file:
        yaml.dump(inventory, file, default_flow_style=False)
    print(f"Ansible inventory file has been created: {inventory_file}")
    return inventory_file


def collect_aws_credentials(existing_creds: dict = None):
    existing_creds = existing_creds or {}
    print("Please provide the AWS credentials given to you by Nanome:")
    access_key = existing_creds.get('aws_access_key', '')
    secret_key = existing_creds.get('aws_secret_key', '')
    masked_access_key = f"{'*' * len(access_key[:-4])}{access_key[-4:]}"
    masked_secret_key = f"{'*' * len(secret_key[:-4])}{secret_key[-4:]}"

    aws_access_key_id = input((
        f"Current AWS Access Key ID: {masked_access_key or 'None'}\n"
        f"New AWS Access Key ID: "
    ))

    aws_secret_access_key_id = getpass.getpass((
        f"Current AWS Secret Access Key: {masked_secret_key or 'None'}\n"
        f"New AWS Secret Access Key ID: "
    ))
    aws_region = 'us-west-1'
    credentials = {
        "aws_access_key": aws_access_key_id,
        "aws_secret_key": aws_secret_access_key_id,
        "region": aws_region
    }
    return credentials


def configure_aws_credentials(inventory_filepath):
    # Get existing AWS credentials from tool server
    existing_aws_creds = retrieve_aws_credentials_from_toolserver(inventory_filepath)
    if existing_aws_creds:
        # If there are existing AWS credentials, ask the user if they want to update them
        overwrite_input = None
        while overwrite_input not in ['1', '2']:
            overwrite_input = input((
                "Your server already has AWS credentials added.\n"
                "How do you want to proceed?\n"
                "1. Use existing credentials\n"
                "2. Update values\n\n"
                "Make a selection (1|2): "
            ))
        update_credentials = overwrite_input == '2'
    else:
        update_credentials = True

    if update_credentials:
        # Collect AWS credentials
        credentials = collect_aws_credentials(existing_aws_creds)

        # Run Ansible Playbook
        playbook_path = os.path.join(PLAYBOOKS_DIR, 'aws_configure.yaml')
        extra_vars = json.dumps(credentials)
        result = subprocess.run([
            'ansible-playbook',
            playbook_path,
            '-i', inventory_filepath,
            '--extra-vars', extra_vars,
            '-b'
        ])
        print(result.stdout)
        if result.returncode != 0:
            print("An error occurred:")
            print(result.stderr)


def generate_random_password(length=16):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))


def main():
    print((
        "\nThanks for using MARA!\n\n"
        "This script will do 2 things:\n"
        "\t- Install Docker on this server.\n"
        "\t- Install AWSCLI on this server, and configure AWS credentials.\n"
        
    ))
    inventory_filepath = os.path.join(os.path.dirname(__file__), 'inventory.local.yaml')
    if not os.path.exists(inventory_filepath):
        mara_host_config = {
            'ansible_host': '127.0.0.1',
            'ansible_user': getpass.getuser(),
            'ansible_connection': 'local'
        }
        print("\nSetting up the Tool Server")
        create_inventory_file(inventory_filepath, mara_host_config)

    print("Installing AWS CLI on your servers...")
    install_awscli_playbook = os.path.join(PLAYBOOKS_DIR, 'install_awscli.yaml')
    subprocess.run([
        'ansible-playbook',
        '-i', inventory_filepath,
        install_awscli_playbook
    ])

    print("Installing Docker on your servers...")
    install_docker_playbook = os.path.join(PLAYBOOKS_DIR, 'install_docker.yaml')
    subprocess.run([
        'ansible-playbook',
        '-i', inventory_filepath,
        install_docker_playbook
    ])


    # Add AWS credentials to the servers
    configure_aws_credentials(inventory_filepath)

    print('AWSCLI has been installed.')

    print("Docker has been Installed! Note you may need to restart this server for changes to take effect.")


if __name__ == "__main__":
    main()
