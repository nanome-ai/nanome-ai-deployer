import getpass

from .utils import generate_random_password, PLAYBOOKS_DIR


def configure_tool_server(existing_env=None) -> dict:
    env = existing_env or {}
    api_key_selection = None

    existing_api_key = existing_env.get('API_KEY', None)
    while api_key_selection not in ['1', '2', '3']:
        api_key_selection = input((
            "\n\nTool Server API Key: How do you want to set up your key?\n"
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
        api_key = existing_api_key
    elif api_key_selection == '3':
        api_key = input("Enter the API Key: ")
    env['API_KEY'] = api_key
    return env


def configure_azure_envvars(mara_env) -> dict:
    llm_api_url = mara_env.get('LLM_API_URL', None)
    embedding_deployment = mara_env.get('EMBEDDING_MODEL', None)
    llm_model = mara_env.get('LLM_MODEL', None)
    azure_llm_api_version = mara_env.get('AZURE_LLM_API_VERSION', None)
    azure_embedding_api_version = mara_env.get('AZURE_EMBEDDING_API_VERSION', None)

    # Collect Azure LLM API URL
    update_value = True
    if llm_api_url:
        modify_answer = input(f'Your current LLM_API_URL is set to {llm_api_url}. Press ENTER to continue, or "1" to modify: ')
        update_value = modify_answer != ''
    if update_value:
        llm_api_url = input("Enter your Azure LLM API URL (e.g https://acme.azure.com/v1): ")

    # Collect Azure EMBEDDING_DEPLOYMENT NAME
    update_value = True
    if embedding_deployment:
        modify_answer = input(f'Your current EMBEDDING_DEPLOYMENT is set to {embedding_deployment}. Press ENTER to continue, or "1" to modify: ')
        update_value = modify_answer != ''
    if update_value:
        embedding_deployment = input('Enter the deployment name for your embedding model (default "text-embedding-ada-002") ') or 'text-embedding-ada-002'

    # Collect Azure GPT-4.1 Deployment name
    update_value = True
    if llm_model:
        modify_answer = input(f'Your current LLM_MODEL is set to {llm_model}. Press ENTER to continue, or "1" to modify: ')
        update_value = modify_answer != ''
    if update_value:
        llm_model = input('Enter the deployment name for your gpt-4.1 model (default "gpt-4.1") ') or 'gpt-4.1'

    # Collect llm api version
    update_value = True
    if azure_llm_api_version:
        modify_answer = input(f'Your current AZURE_EMBEDDING_API_VERSION is set to {azure_llm_api_version}. Press ENTER to continue, or "1" to modify: ')
        update_value = modify_answer != ''
    if update_value:
        azure_llm_api_version = input('Enter the API version for your LLM (default "2024-08-01-preview") ') or '2024-08-01-preview'

    # Collect embedding api version
    update_value = True
    if azure_embedding_api_version:
        modify_answer = input(f'Your current AZURE_EMBEDDING_API_VERSION is set to {azure_embedding_api_version}. Press ENTER to continue, or "1" to modify: ')
        update_value = modify_answer != ''
    if update_value:
        azure_embedding_api_version = input('Enter the API version for your embedding model (default "2023-05-15") ') or '2023-05-15'

    env = {
        'OPENAI_API_TYPE': 'azure',
        'LLM_API_URL': llm_api_url,
        'AZURE_EMBEDDING_API_VERSION': azure_embedding_api_version,
        'AZURE_LLM_API_VERSION': azure_llm_api_version,
        'EMBEDDING_MODEL': embedding_deployment,
        'LLM_MODEL': llm_model,
        'LLM_MODEL_MD': llm_model,
        'LLM_MODEL_SM': llm_model,
    }
    return env

def configure_mara_server(existing_mara_env) -> dict:
    env = {}

    # Ask if the user wants to set up AI features
    enable_ai = None
    while enable_ai not in ['1', '2']:
        enable_ai = input((
            '\n\nWould you like to set up AI chat features?\n'
            '1. Yes\n'
            '2. No (workspace management only)\n\n'
            'Make a selection (1|2): '
        ))

    if enable_ai == '2':
        env['LLM_API_KEY'] = ''
        return env

    azure_provider = None
    while azure_provider not in ['1', '2']:
        azure_provider = input((
            '\n\nWill you be using Microsoft Azure-hosted LLMs?\n'
            '1. Yes\n'
            '2. No\n\n'
            'Make a selection (1|2): '
        ))
    if azure_provider == '1':
        azure_env_vars = configure_azure_envvars(existing_mara_env)
        env.update(azure_env_vars)

    exisitng_llm_key = existing_mara_env.get('LLM_API_KEY', None)
    llm_key_option = None
    if not exisitng_llm_key:
        llm_key_option = '2'
    while llm_key_option not in ['1', '2']:
        llm_key_option = input((
            '\n\nLLM API Key (1|2)\n'
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

    env.update({
        'LLM_API_KEY': llm_key,
    })
    return env
