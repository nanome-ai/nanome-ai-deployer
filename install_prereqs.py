import getpass
import json
import os
import subprocess

from cli.utils import PLAYBOOKS_DIR, create_inventory_file, collect_aws_credentials, get_existing_aws_credentials


def configure_aws_credentials(inventory_filepath):
    # Get existing AWS credentials from tool server
    existing_aws_creds = get_existing_aws_credentials()
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


def main():
    print((
        "\nThanks for using MARA!\n\n"
        "This script will do 2 things:\n"
        "\t- Install Docker on this server.\n"
        "\t- Install AWSCLI on this server, and configure AWS credentials.\n"
        
    ))
    input('Press ENTER to continue...')
    inventory_filepath = os.path.join(os.path.dirname(__file__), 'inventory.local.yaml')
    if not os.path.exists(inventory_filepath):
        mara_host_config = {
            'ansible_host': '127.0.0.1',
            'ansible_user': getpass.getuser(),
            'ansible_connection': 'local'
        }
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

    print("Docker has been installed! Note you may need to restart this server for changes to take effect.")


if __name__ == "__main__":
    main()
