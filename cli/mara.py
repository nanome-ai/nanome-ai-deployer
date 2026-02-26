import getpass

from .utils import ask_selection, generate_random_password, PLAYBOOKS_DIR


def configure_tool_server(existing_env=None) -> dict:
    env = existing_env or {}
    existing_api_key = env.get('API_KEY', None)
    if not existing_api_key:
        env['API_KEY'] = generate_random_password(40)
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
        modify_answer = input(f'\nLLM_API_URL is set to "{llm_api_url}".\nPress ENTER to continue, or "1" to modify: ')
        update_value = modify_answer != ''
    if update_value:
        llm_api_url = input("\nEnter your Azure LLM API URL\n(e.g https://example.azure.com/v1): ")

    # Collect Azure EMBEDDING_DEPLOYMENT NAME
    update_value = True
    if embedding_deployment:
        modify_answer = input(f'\nEMBEDDING_DEPLOYMENT is set to "{embedding_deployment}".\nPress ENTER to continue, or "1" to modify: ')
        update_value = modify_answer != ''
    if update_value:
        embedding_deployment = input('\nEnter the deployment name for your embedding model\n[text-embedding-ada-002]: ') or 'text-embedding-ada-002'

    # Collect Azure GPT-4.1 Deployment name
    update_value = True
    if llm_model:
        modify_answer = input(f'\nLLM_MODEL is set to "{llm_model}".\nPress ENTER to continue, or "1" to modify: ')
        update_value = modify_answer != ''
    if update_value:
        llm_model = input('\nEnter the deployment name for your gpt-4.1 model\n[gpt-4.1]: ') or 'gpt-4.1'

    # Collect llm api version
    update_value = True
    if azure_llm_api_version:
        modify_answer = input(f'\nAZURE_LLM_API_VERSION is set to "{azure_llm_api_version}".\nPress ENTER to continue, or "1" to modify: ')
        update_value = modify_answer != ''
    if update_value:
        azure_llm_api_version = input('\nEnter the API version for your LLM\n[2024-08-01-preview]: ') or '2024-08-01-preview'

    # Collect embedding api version
    update_value = True
    if azure_embedding_api_version:
        modify_answer = input(f'\nAZURE_EMBEDDING_API_VERSION is set to "{azure_embedding_api_version}".\nPress ENTER to continue, or "1" to modify: ')
        update_value = modify_answer != ''
    if update_value:
        azure_embedding_api_version = input('\nEnter the API version for your embedding model\n[2023-05-15]: ') or '2023-05-15'

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

    existing_llm_key = existing_mara_env.get('LLM_API_KEY', None)
    existing_is_azure = existing_mara_env.get('OPENAI_API_TYPE', '').lower() == 'azure'

    # Ask if the user wants to set up AI features
    enable_ai = ask_selection(
        'Would you like to set up AI chat features?',
        ['Yes', 'No (workspace management only)'],
        default=2 if existing_llm_key == '' else 1,
    )

    if enable_ai == '2':
        env['LLM_API_KEY'] = ''
        return env

    llm_provider = ask_selection(
        'Which LLM provider are you using?',
        ['OpenAI', 'Microsoft Azure (Foundry)'],
        default=2 if existing_is_azure else 1,
    )
    if llm_provider == '2':
        azure_env_vars = configure_azure_envvars(existing_mara_env)
        env.update(azure_env_vars)

    if not existing_llm_key:
        llm_key_option = '2'
    else:
        llm_key_option = ask_selection(
            'LLM API Key',
            ['Use existing key', 'Update key'],
            default=1,
        )

    if llm_key_option == '1':
        llm_key = existing_llm_key
    else:
        if not existing_llm_key:
            llm_key = getpass.getpass("\nEnter LLM_API_KEY (input will not be visible): ")
        else:
            masked_llm_key = f"{'*' * len(existing_llm_key[:-4])}{existing_llm_key[-4:]}"
            llm_key = getpass.getpass((
                f"\nCurrent LLM_API_KEY: {masked_llm_key or 'None'}"
                "\nNew LLM_API_KEY (input will not be visible): "
            ))

    env.update({
        'LLM_API_KEY': llm_key,
    })
    return env
