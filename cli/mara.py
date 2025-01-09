import getpass

from .utils import generate_random_password, PLAYBOOKS_DIR


def configure_tool_server(existing_env=None) -> dict:
    env = existing_env or {}
    api_key_selection = None

    existing_api_key = existing_env.get('API_KEY', None)
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
        api_key = existing_api_key
    elif api_key_selection == '3':
        api_key = input("Enter the API Key: ")
    env['API_KEY'] = api_key
    return env


def configure_mara_server(existing_mara_env, tool_server_api_key) -> dict:
    azure_provider = None
    env = {}
    while azure_provider not in ['1', '2']:
        azure_provider = input((
            'Will you be using a Microsoft Azure-hosted LLM such as GPT4?\n'
            '1. Yes\n'
            '2. No\n\n'
            'Make a selection (1|2): '
        ))
    if azure_provider == '1':
        env['OPENAI_API_TYPE'] = 'azure'
        llm_url = input("Enter your Azure LLM API URL (e.g https://acme.azure.com/v1): ")
        env['LLM_API_URL'] = llm_url

    exisitng_llm_key = existing_mara_env.get('LLM_API_KEY', None)
    llm_key_option = None
    if not exisitng_llm_key:
        llm_key_option = '2'
    while llm_key_option not in ['1', '2']:
        llm_key_option = input((
            '\nLLM API Key (1|2)\n'
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
        'TOOL_SERVER_KEY': tool_server_api_key
    })
    return env
