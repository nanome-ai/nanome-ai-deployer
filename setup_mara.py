import getpass
import json
import os
import random
import string
import subprocess
import tempfile
import yaml


PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), 'playbooks')


def gather_user_input():
    # Get ip address of remote server
    ip_address = input("Enter the server IP address: ")
    # Ask for the username to log into the server
    username = input("Enter the username for SSH login: ")
    # Ask for the path to the private key file
    private_key_file = input("Enter the path to your Identity key file (e.g., /home/user/.ssh/id_rsa): ")

    # Ensure that the private key file exists
    if not os.path.isfile(private_key_file):
        print(f"Error: The private key file {private_key_file} does not exist.")
        return

    https_input = input("Do you want to configure https? (yes/no): ")
    https_enabled = https_input.lower() == 'yes'

    certs_path = None
    if https_enabled:
        certs_path = input("Enter the path to the directory where the SSL certificates are stored: ")

    host_config = {
        'ansible_host': ip_address,
        'ansible_user': username,
        'ansible_ssh_private_key_file': private_key_file,
        'https_enabled': https_enabled
    }
    if https_enabled:
        host_config['certs_path'] = certs_path

    return host_config


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


def collect_aws_credentials(existing_creds: dict):
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


def generate_random_password(length=16):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))


def retrieve_aws_credentials_from_toolserver(inventory_filepath):
    playbook_path = os.path.join(PLAYBOOKS_DIR, 'retrieve_aws_creds_from_toolserver.yaml')
    aws_creds = {}
    with tempfile.NamedTemporaryFile(suffix='.yaml') as f:
        cmd = [
            'ansible-playbook',
            playbook_path,
            '-i', inventory_filepath,
            '--extra-vars', f'output_yaml={f.name}'
        ]
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print("An error occurred:")
            print(result.stderr)
            return aws_creds
        with open(f.name, 'r') as f:
            aws_creds = yaml.safe_load(f)
        return aws_creds


def retrieve_api_key_from_toolserver(inventory_filepath):
    playbook_path = os.path.join(PLAYBOOKS_DIR, 'retrieve_api_key_from_toolserver.yaml')
    with tempfile.NamedTemporaryFile(suffix='.txt') as f:
        cmd = [
            'ansible-playbook',
            playbook_path,
            '-i', inventory_filepath,
            '--extra-vars', f'api_key_txt={f.name}'
        ]
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print("An error occurred:")
            print(result.stderr)
        with open(f.name, 'r') as f:
            api_key = f.read()
        return api_key


def retrieve_llm_api_key_from_mara(inventory_filepath):
    playbook_path = os.path.join(PLAYBOOKS_DIR, 'retrieve_llm_api_key_from_mara.yaml')
    with tempfile.NamedTemporaryFile(suffix='.txt') as f:
        cmd = [
            'ansible-playbook',
            playbook_path,
            '-i', inventory_filepath,
            '--extra-vars', f'llm_api_key_txt={f.name}'
        ]
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print("An error occurred:")
            print(result.stderr)
        with open(f.name, 'r') as f:
            llm_api_key = f.read()
        return llm_api_key

def configure_workspace_api(inventory_filepath):
    deploy_workspace_api_playbook = os.path.join(PLAYBOOKS_DIR, 'deploy_workspace_api.yaml')
    subprocess.run([
        'ansible-playbook',
        '-i', inventory_filepath,
        deploy_workspace_api_playbook
    ])

def configure_workspace_load_service(inventory_filepath):
    deploy_workspace_load_service_playbook = os.path.join(PLAYBOOKS_DIR, 'deploy_workspace_load_service.yaml')
    subprocess.run([
        'ansible-playbook',
        '-i', inventory_filepath,
        deploy_workspace_load_service_playbook
    ])

def configure_tool_server(inventory_filepath, api_key_file=''):
    api_key_selection = None
    while api_key_selection not in ['1', '2', '3']:
        api_key_selection = input((
            "Tool Server API Key: How do you want to set up your key?\n"
            "1. Generate new key automatically (Recommended for first time deployments):\n"
            "2. Use existing key already on server (Recommended for redeployments):\n"
            "3. Type new key manually\n\n"
            "Make a selection (1|2|3): "
        ))

    api_key = None
    if api_key_selection == '1':
        api_key = generate_random_password(40)
        print(f"Generated new API Key")
    elif api_key_selection == '2':
        api_key = retrieve_api_key_from_toolserver(inventory_filepath)
    elif api_key_selection == '3':
        api_key = input("Enter the API Key: ")

    # Write .env file
    env_file = os.path.join(os.path.dirname(__file__), '.env.toolserver')
    with open(env_file, 'w') as f:
        f.write(f'API_KEY={api_key}')
        # write api key to local file for later use
        if api_key_file:
            with open(api_key_file, 'w') as f:
                f.write(api_key)
    # Run Ansible Playbook
    playbook_path = os.path.join(PLAYBOOKS_DIR, 'deploy_tool_server.yaml')
    cmd = [
        'ansible-playbook',
        playbook_path,
        '-i', inventory_filepath,
    ]
    if api_key:
        cmd.extend(['--extra-vars', f'env_file={env_file}'])
    subprocess.run(cmd)
    os.remove(env_file)


def configure_mara_server(inventory_filepath, tool_server_api_key):
    azure_provider = input((
        'Will you be using a Microsoft Azure-hosted LLM such as GPT4?\n'
        '1. Yes\n'
        '2. No\n\n'
        'Make a selection (1|2): '
    ))
    env_var_values = {}
    if azure_provider == '1':
        env_var_values['OPENAI_API_TYPE'] = 'azure'
        llm_url = input("Enter your Azure LLM API URL (e.g https://acme.azure.com/v1): ")
        env_var_values['LLM_API_URL'] = llm_url

    exisitng_llm_key = retrieve_llm_api_key_from_mara(inventory_filepath)
    llm_key_option = None
    if not exisitng_llm_key:
        llm_key_option = '2'
    while llm_key_option not in ['1', '2']:
        llm_key_option = input((
            'LLM API Key (1|2)\n'
            '1. Use existing key on server (Recommended for redeployments):\n'
            '2. Add/Update Key\n\n'
            'Make a selection (1|2): '
        ))
    if llm_key_option == '1':
        llm_key = exisitng_llm_key
    else:
        if not exisitng_llm_key:
            llm_key = getpass.getpass("Enter the API_KEY for your LLM Provider: ")
        else:
            masked_llm_key = f"{'*' * len(exisitng_llm_key[:-4])}{exisitng_llm_key[-4:]}"
            llm_key = getpass.getpass((
                f"Current LLM_API_KEY: {masked_llm_key or 'None'}\n"
                "New LLM_API_KEY: "
            ))

    tool_server_url = 'http://127.0.0.1:8001'
    workspace_api_url = 'http://127.0.0.1:8002'
    # Write to .env file
    env_file = os.path.join(os.path.dirname(__file__), '.env.maraserver')

    env_var_values.update({
        'LLM_API_KEY': llm_key,
        'TOOL_SERVER_URL': tool_server_url,
        'TOOL_SERVER_KEY': tool_server_api_key,
        'NANOME_SERVICES_URL': workspace_api_url
    })
    with open(env_file, 'w') as f:
        env_content = '\n'.join([f'{k}={v}' for k, v in env_var_values.items()])
        f.write(env_content)

    # Run Ansible Playbook
    playbook_path = os.path.join(PLAYBOOKS_DIR, 'deploy_mara.yaml')
    cmd = [
        'ansible-playbook',
        playbook_path,
        '-i', inventory_filepath,
        '--extra-vars', f'env_file={env_file}'
    ]
    subprocess.run(cmd)
    os.remove(env_file)


def main():
    print(
        "\nThanks for using MARA! Let's get started setting up your server!\n"
        "This script will download and run 4 docker containers:\n"
        "\t- Workspace API: Acts as a data store of Nanome workspaces.\n"
        "\t- Workspace Load Service: Contains business logic for rendering structure files as a Nanome workspace.\n"
        "\t- Tool Server: Runs computations for MARA workflows.\n"
        "\t- MARA: Web Application and API for performing comp-chem workflows.\n"
    )
    input('Press any key to continue')
    inventory_filepath = os.path.join(os.path.dirname(__file__), 'inventory.local.yaml')
    if not os.path.exists(inventory_filepath):
        mara_host_config = {
            'ansible_host': '127.0.0.1',
            'ansible_user': 'ec2-user',
            'ansible_connection': 'local'
        }
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
