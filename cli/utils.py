import sys
import certifi
import getpass
import os
import random
import string
import urllib.request
import yaml

PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), 'playbooks')


def ask_selection(question, options, default=None):
    """Prompt the user to select from numbered options.

    Args:
        question: The question text to display.
        options: List of option labels (displayed as 1., 2., etc.).
        default: 1-indexed default option number, or None.

    Returns:
        The selected option number as a string ('1', '2', etc.).
    """
    option_lines = '\n'.join(f'{i}. {opt}' for i, opt in enumerate(options, 1))
    default_hint = f' [{default}]' if default else ''

    valid = [str(i) for i in range(1, len(options) + 1)]
    if default:
        valid.append('')

    selection = None
    while selection not in valid:
        selection = input(
            f'\n\n{question}\n'
            f'{option_lines}\n\n'
            f'Make a selection{default_hint}: '
        )

    return selection if selection != '' else str(default)


def extract_host_from_env(env_dict, prefix):
    """Extract the base host from a VIRTUAL_HOST value by stripping a known prefix.

    e.g. VIRTUAL_HOST='nanome.company.com' with prefix='nanome' -> 'company.com'
    """
    virtual_host = env_dict.get('VIRTUAL_HOST', '')
    expected_prefix = f'{prefix}.'
    if virtual_host.startswith(expected_prefix):
        return virtual_host[len(expected_prefix):]
    return None


def gather_host_info(default=None):
    default_hint = f'[{default}]' if default else '(defaults to <IP>.nip.io)'
    host = input(f'\n\nWhat domain name will you be using to access? (e.g. example.com)\nEnter domain {default_hint}: ')
    if not host and default:
        host = default
    elif not host:
        host = get_public_ip() + '.nip.io'
    return host


def generate_random_password(length=16):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(length))


def check_certs(path, name, enforce=False):
    for ext in ['crt', 'key']:
        cert_path = os.path.join(path, f'{name}.{ext}')
        if not os.path.exists(cert_path):
            return False
        # check if PEM format
        with open(cert_path, 'r') as f:
            content = f.read()
            if ext == 'crt' and '-----BEGIN CERTIFICATE-----' not in content:
                if enforce:
                    print(f"Certificate {name}.{ext} must be in PEM format.")
                    sys.exit(1)
                return False
            if ext == 'key' and '-----BEGIN PRIVATE KEY-----' not in content:
                if enforce:
                    print(f"Private key {name}.{ext} must be in PEM format.")
                    sys.exit(1)
                return False
    return True


def has_default_certs(path, enforce=False):
    return check_certs(path, 'default', enforce=enforce)


def has_individual_certs(path, enforce=False):
    has_certs = True
    for name in ['nanome', 'nanome-tools', 'workspaces']:
        if not check_certs(path, name, enforce=enforce):
            has_certs = False
            break
    return has_certs


def gather_https_info(host):
    use_existing = None
    has_default = has_default_certs('./certs')
    has_individual = has_individual_certs('./certs')
    if has_default or has_individual:
        use_existing = ask_selection(
            "Found existing TLS certificates in ./certs\n"
            "Would you like to use these for HTTPS?",
            ['Yes', 'No'],
            default=1,
        )

    if use_existing != '1':
        https_input = ask_selection(
            "Do you have local TLS certificates you would like to use for HTTPS?",
            ['Yes', 'No'],
            default=2,
        )
        if https_input != '1':
            return 'None'

    while True:
        if use_existing != '1':
            certs_path = input(
                "\n\nEnter path containing either:\n"
                f"  default.crt/default.key covering *.{host}\n"
                "or\n"
                f"  nanome.crt/nanome.key covering nanome.{host}\n"
                f"  nanome-tools.crt/nanome-tools.key covering nanome-tools.{host}\n"
                f"  workspaces.crt/workspaces.key covering workspaces.{host}\n"
                "\nEnter path: "
            )

            has_default = has_default_certs(certs_path)
            has_individual = has_individual_certs(certs_path)
            if not (has_default or has_individual):
                print("Could not find valid certificates in the provided path. Please try again.")
                continue

            # copy certs to ./certs
            os.makedirs('./certs', exist_ok=True)
            if has_default:
                check_certs(certs_path, 'default', enforce=True)
                with open(os.path.join(certs_path, 'default.crt'), 'rb') as src_cert:
                    with open('./certs/default.crt', 'wb') as dest_cert:
                        dest_cert.write(src_cert.read())
                with open(os.path.join(certs_path, 'default.key'), 'rb') as src_key:
                    with open('./certs/default.key', 'wb') as dest_key:
                        dest_key.write(src_key.read())
                print("Copied default certificates to ./certs.")
            elif has_individual:
                for name in ['nanome', 'nanome-tools', 'workspaces']:
                    check_certs(certs_path, name, enforce=True)
                    with open(os.path.join(certs_path, f'{name}.crt'), 'rb') as src_cert:
                        with open(f'./certs/{name}.crt', 'wb') as dest_cert:
                            dest_cert.write(src_cert.read())
                    with open(os.path.join(certs_path, f'{name}.key'), 'rb') as src_key:
                        with open(f'./certs/{name}.key', 'wb') as dest_key:
                            dest_key.write(src_key.read())
                print("Copied individual certificates to ./certs.")

        # create a bundle.pem file for requests
        with open('./certs/bundle.pem', 'w') as bundle_file:
            with open(certifi.where(), 'r') as ca_file:
                bundle_file.write(ca_file.read())
            if has_default:
                with open('./certs/default.crt', 'r') as cert_file:
                    bundle_file.write(cert_file.read())
            elif has_individual:
                for name in ['nanome', 'nanome-tools', 'workspaces']:
                    with open(f'./certs/{name}.crt', 'r') as cert_file:
                        bundle_file.write(cert_file.read())

        return 'Default' if has_default else 'Individual'


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


def write_env_file(env_filepath, env_dict: dict, append=False) -> None:
    """Write a dict to a .env file."""
    write_mode = 'a' if append else 'w'
    with open(env_filepath, write_mode) as f:
        for key, value in env_dict.items():
            line = f'{key}={value}\n'
            f.write(line)


def get_public_ip():
    """Get public ip from api.ipify.org."""
    ip_lookup_url = "https://api.ipify.org"
    try:
        with urllib.request.urlopen(ip_lookup_url) as response:
            return response.read().decode("utf-8")
    except Exception as e:
        print(f"Error fetching public IP: {e}")
        return None
