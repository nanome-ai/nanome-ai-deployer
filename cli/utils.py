import getpass
import os
import random
import string
import yaml


PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), 'playbooks')


def generate_random_password(length=16):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))


def gather_https_info():
    https_input = None
    while https_input not in ['1', '2']:
        https_input = input(
            "\nDo you want to configure https?\n"
            "1. Yes\n"
            "2. No\n"
            "Make a selection (1|2): "
        )
    https_enabled = https_input == '1'

    certs_path = None
    if https_enabled:
        certs_path = input("Enter the path to the directory where the SSL certificates are stored: ")

    host_config = {
        'https_enabled': https_enabled
    }
    if https_enabled:
        host_config['certs_path'] = certs_path

    return host_config


def create_inventory_file(inventory_file, mara_host_config):
    """Construct an Ansible inventory file with the given host configuration."""
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


def get_existing_aws_credentials():
    """Find existing AWS credentials configured on the server."""
    credentials = {}
    # Check environment variables
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    if access_key and secret_key:
        credentials["aws_access_key"] = access_key
        credentials["aws_secret_key"] = secret_key
        return credentials

    # Check AWS credentials file
    aws_credentials_path = os.path.expanduser("~/.aws/credentials")
    if os.path.exists(aws_credentials_path):
        try:
            with open(aws_credentials_path, "r") as cred_file:
                lines = cred_file.readlines()
                for line in lines:
                    if line.strip().startswith("aws_access_key_id"):
                        credentials["aws_access_key"] = line.split("=", 1)[1].strip()
                    if line.strip().startswith("aws_secret_access_key"):
                        credentials["aws_secret_key"] = line.split("=", 1)[1].strip()
                if "access_key" in credentials and "secret_key" in credentials:
                    return credentials
        except Exception as e:
            print(f"Error reading AWS credentials file: {e}")
    return credentials


def read_env_file(file_path):
    """Reads a .env file and converts its content to a dictionary.
    
    Args:
        file_path (str): The path to the .env file.
    
    Returns:
        dict: A dictionary containing key-value pairs from the .env file.
    """
    env_dict = {}
    
    if not os.path.exists(file_path):
        return env_dict
    
    with open(file_path, 'r') as file:
        for line in file:
            # Strip whitespace and skip empty lines or comments
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Split by the first `=` sign
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")  # Remove surrounding quotes if any
                env_dict[key] = value
    return env_dict
