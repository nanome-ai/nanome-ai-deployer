import getpass
import os
import subprocess
import tempfile

from .utils import generate_random_password, PLAYBOOKS_DIR


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
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env.toolserver')
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
    # os.remove(env_file)


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
    env_file = os.path.join(os.path.dirname(__file__), '..', '.env.maraserver')

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
    # os.remove(env_file)

