import getpass
import json

from .utils import ask_selection, generate_random_password, PLAYBOOKS_DIR


# Keys this file is responsible for. Anything here gets cleared from the env on
# each run before the new selections are written, so switching providers (e.g.
# OpenAI -> Anthropic, or Azure api_key -> service_principal) doesn't leave
# stale settings behind.
PROVIDER_ENV_KEYS = (
    'OPENAI_API_TYPE',
    'LLM_API_URL',
    'LLM_API_KEY',
    'LLM_API_HEADERS',
    'LLM_MODEL',
    'LLM_MODEL_MD',
    'LLM_MODEL_SM',
    'EMBEDDING_MODEL',
    'AWS_AUTH_MODE',
    'AWS_REGION',
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'AWS_SESSION_TOKEN',
    'AZURE_LLM_API_VERSION',
    'AZURE_EMBEDDING_API_VERSION',
    'AZURE_AUTH_MODE',
    'AZURE_TENANT_ID',
    'AZURE_CLIENT_ID',
    'AZURE_CLIENT_SECRET',
    'AZURE_TOKEN_SCOPE',
)


def configure_tool_server(existing_env=None) -> dict:
    env = existing_env or {}
    existing_api_key = env.get('API_KEY', None)
    if not existing_api_key:
        env['API_KEY'] = generate_random_password(40)
    return env


def _prompt_with_default(label, current, default=None, is_secret=False):
    """Show current value (masked if secret), accept ENTER to keep, or new input."""
    prompt_fn = getpass.getpass if is_secret else input
    if current:
        display = f"{'*' * len(current[:-4])}{current[-4:]}" if is_secret else current
        modify = input(f'\n{label} is set to "{display}".\nPress ENTER to keep, or "1" to modify: ')
        if modify == '':
            return current
    hint = f' [{default}]' if default else ''
    value = prompt_fn(f'\nEnter {label}{hint}: ')
    if not value and default is not None:
        value = default
    return value


def _ensure_provider_prefix(model, provider):
    """Force a ``provider:model`` string."""
    if not model:
        return model
    return f'{provider}:{model}'


# Three model tiers used across the codebase. The labels below get appended to
# each prompt so the operator can reason about which deployment to map.
TIER_PROMPTS = (
    ('LLM_MODEL', 'reasoning and planning'),
    ('LLM_MODEL_MD', 'plan execution'),
    ('LLM_MODEL_SM', 'classification and routing'),
)


def _prompt_model_tiers(mara_env, defaults, label_prefix='', provider_prefix=None):
    """Prompt for LLM/MD/SM model deployments with per-tier defaults.

    ``defaults`` is a 3-tuple aligned with ``TIER_PROMPTS``. ``label_prefix``
    lets the Azure flow tag prompts as deployment names. ``provider_prefix``
    forces ``provider:model`` strings (used for Anthropic).
    """
    out = {}
    for (key, purpose), default in zip(TIER_PROMPTS, defaults):
        label = f'{key}{label_prefix} ({purpose})'
        value = _prompt_with_default(label, mara_env.get(key), default=default)
        if provider_prefix:
            value = _ensure_provider_prefix(value, provider_prefix)
        out[key] = value
    return out


def configure_openai_envvars(mara_env) -> dict:
    """Plain OpenAI (or any OpenAI-compatible endpoint, e.g. self-hosted vLLM)."""
    llm_api_url = _prompt_with_default(
        'LLM_API_URL',
        mara_env.get('LLM_API_URL'),
        default='https://api.openai.com/v1',
    )
    tiers = _prompt_model_tiers(
        mara_env,
        defaults=('gpt-5.5', 'gpt-5.4-mini', 'gpt-5.4-mini'),
    )
    return {'LLM_API_URL': llm_api_url, **tiers}


def configure_anthropic_envvars(mara_env) -> dict:
    """Anthropic API. Uses LLM_API_KEY for the Anthropic key.

    Models are stored as ``anthropic:<name>`` so the provider-aware client
    factory routes correctly even if other settings change later.
    """
    return _prompt_model_tiers(
        mara_env,
        defaults=(
            'claude-opus-4-7',
            'claude-sonnet-4-6',
            'claude-haiku-4-5',
        ),
        provider_prefix='anthropic',
    )


def configure_bedrock_envvars(mara_env) -> dict:
    """AWS Bedrock. Reuses the Anthropic Messages API surface through the
    ``anthropic[bedrock]`` SDK, so only the model IDs and AWS auth differ.

    Models are stored as ``bedrock:<bedrock-model-id>``..
    """
    env: dict = {}

    print("\nNote: current only Anthropic Claude models on Bedrock are supported.")

    region = _prompt_with_default(
        'AWS_REGION',
        mara_env.get('AWS_REGION'),
        default='us-east-1',
    )
    env['AWS_REGION'] = region

    tiers = _prompt_model_tiers(
        mara_env,
        defaults=(
            'anthropic.claude-opus-4-7',
            'anthropic.claude-sonnet-4-6',
            'anthropic.claude-haiku-4-5-20251001-v1:0',
        ),
        provider_prefix='bedrock',
    )
    env.update(tiers)

    # Auth: access keys only
    env['AWS_AUTH_MODE'] = 'access_key'
    env['AWS_ACCESS_KEY_ID'] = _prompt_with_default(
        'AWS_ACCESS_KEY_ID', mara_env.get('AWS_ACCESS_KEY_ID'),
    )
    env['AWS_SECRET_ACCESS_KEY'] = _prompt_with_default(
        'AWS_SECRET_ACCESS_KEY',
        mara_env.get('AWS_SECRET_ACCESS_KEY'),
        is_secret=True,
    )
    session_token = _prompt_with_default(
        'AWS_SESSION_TOKEN (optional, leave blank if not using temporary creds)',
        mara_env.get('AWS_SESSION_TOKEN'),
        is_secret=True,
    )
    if session_token:
        env['AWS_SESSION_TOKEN'] = session_token

    return env


def configure_azure_envvars(mara_env) -> dict:
    """AOAI directly, or AOAI fronted by Azure API Management.

    Returns the deployment-name + version env, the chosen auth mode, and any
    APIM-related headers. The caller is responsible for collecting LLM_API_KEY
    when ``AZURE_AUTH_MODE`` ends up as ``api_key``.
    """
    llm_api_url = _prompt_with_default(
        'LLM_API_URL',
        mara_env.get('LLM_API_URL'),
    ) or input("\nEnter your Azure LLM API URL\n(e.g. https://example.azure.com or https://<apim>.azure-api.net): ")

    embedding_deployment = _prompt_with_default(
        'EMBEDDING_MODEL (Azure deployment name)',
        mara_env.get('EMBEDDING_MODEL'),
        default='text-embedding-ada-002',
    )
    tiers = _prompt_model_tiers(
        mara_env,
        defaults=('gpt-5.4', 'gpt-5.4-mini', 'gpt-5.4-mini'),
        label_prefix=' (Azure deployment name)',
    )
    azure_llm_api_version = _prompt_with_default(
        'AZURE_LLM_API_VERSION',
        mara_env.get('AZURE_LLM_API_VERSION'),
        default='2024-08-01-preview',
    )
    azure_embedding_api_version = _prompt_with_default(
        'AZURE_EMBEDDING_API_VERSION',
        mara_env.get('AZURE_EMBEDDING_API_VERSION'),
        default='2023-05-15',
    )

    env = {
        'OPENAI_API_TYPE': 'azure',
        'LLM_API_URL': llm_api_url,
        'AZURE_EMBEDDING_API_VERSION': azure_embedding_api_version,
        'AZURE_LLM_API_VERSION': azure_llm_api_version,
        'EMBEDDING_MODEL': embedding_deployment,
        **tiers,
    }

    # Auth method
    existing_mode = mara_env.get('AZURE_AUTH_MODE', 'api_key').lower()
    default_choice = {'api_key': 1, 'service_principal': 2}.get(existing_mode, 1)
    auth_choice = ask_selection(
        'How should the container authenticate to Azure?',
        [
            'API key (LLM_API_KEY)',
            'Service Principal (tenant + client id + client secret)',
        ],
        default=default_choice,
    )

    if auth_choice == '1':
        env['AZURE_AUTH_MODE'] = 'api_key'
    else:
        env['AZURE_AUTH_MODE'] = 'service_principal'
        env['AZURE_TENANT_ID'] = _prompt_with_default(
            'AZURE_TENANT_ID', mara_env.get('AZURE_TENANT_ID'),
        )
        env['AZURE_CLIENT_ID'] = _prompt_with_default(
            'AZURE_CLIENT_ID', mara_env.get('AZURE_CLIENT_ID'),
        )
        env['AZURE_CLIENT_SECRET'] = _prompt_with_default(
            'AZURE_CLIENT_SECRET',
            mara_env.get('AZURE_CLIENT_SECRET'),
            is_secret=True,
        )
        env['AZURE_TOKEN_SCOPE'] = _prompt_with_default(
            'AZURE_TOKEN_SCOPE',
            mara_env.get('AZURE_TOKEN_SCOPE'),
            default='https://cognitiveservices.azure.com/.default',
        )

    # APIM subscription key (optional, layered on top of the auth above)
    use_apim_key = ask_selection(
        'Is your endpoint fronted by APIM with a subscription key?',
        ['No', 'Yes'],
        default=2 if mara_env.get('LLM_API_HEADERS') else 1,
    )
    if use_apim_key == '2':
        existing_headers = mara_env.get('LLM_API_HEADERS') or ''
        existing_sub_key = ''
        try:
            parsed = json.loads(existing_headers) if existing_headers else {}
            existing_sub_key = parsed.get('Ocp-Apim-Subscription-Key', '')
        except json.JSONDecodeError:
            pass
        sub_key = _prompt_with_default(
            'APIM subscription key (Ocp-Apim-Subscription-Key)',
            existing_sub_key,
            is_secret=True,
        )
        if sub_key:
            env['LLM_API_HEADERS'] = json.dumps({'Ocp-Apim-Subscription-Key': sub_key})

    return env


def _collect_llm_api_key(existing_mara_env) -> str:
    existing_llm_key = existing_mara_env.get('LLM_API_KEY', None)
    if not existing_llm_key:
        return getpass.getpass("\nEnter LLM_API_KEY (input will not be visible): ")

    choice = ask_selection(
        'LLM API Key',
        ['Use existing key', 'Update key'],
        default=1,
    )
    if choice == '1':
        return existing_llm_key
    masked = f"{'*' * len(existing_llm_key[:-4])}{existing_llm_key[-4:]}"
    return getpass.getpass((
        f"\nCurrent LLM_API_KEY: {masked or 'None'}"
        "\nNew LLM_API_KEY (input will not be visible): "
    ))


def configure_mara_server(existing_mara_env) -> dict:
    # Strip every provider-related key from the existing env. The function
    # rebuilds them based on the user's current selections; leaving stale keys
    # in (e.g. LLM_API_KEY when switching to service_principal, or AZURE_* when
    # switching to Anthropic) silently breaks runtime config.
    base_env = {k: v for k, v in existing_mara_env.items() if k not in PROVIDER_ENV_KEYS}
    env = dict(base_env)

    # Detect prior provider for the default selection
    prior_type = (existing_mara_env.get('OPENAI_API_TYPE') or '').lower()
    prior_model = existing_mara_env.get('LLM_MODEL') or ''
    if prior_type == 'azure':
        prior_provider = 4
    elif prior_model.startswith('bedrock:'):
        prior_provider = 3
    elif prior_model.startswith('anthropic:'):
        prior_provider = 1
    else:
        prior_provider = 2

    existing_llm_key = existing_mara_env.get('LLM_API_KEY', None)
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
        ['Anthropic', 'OpenAI', 'AWS Bedrock', 'Microsoft Foundry (Azure)'],
        default=prior_provider,
    )

    same_provider = llm_provider == str(prior_provider)
    config_env = existing_mara_env if same_provider else base_env

    if llm_provider == '1':
        env.update(configure_anthropic_envvars(config_env))
        env['LLM_API_KEY'] = _collect_llm_api_key(config_env)
    elif llm_provider == '2':
        env.update(configure_openai_envvars(config_env))
        env['LLM_API_KEY'] = _collect_llm_api_key(config_env)
    elif llm_provider == '3':
        # Bedrock authenticates via AWS creds, not LLM_API_KEY.
        env.update(configure_bedrock_envvars(config_env))
    elif llm_provider == '4':
        provider_env = configure_azure_envvars(config_env)
        env.update(provider_env)
        # Service principal / managed identity flows authenticate via Entra
        # tokens; no static API key is needed (or wanted) in that case.
        if provider_env.get('AZURE_AUTH_MODE') == 'api_key':
            env['LLM_API_KEY'] = _collect_llm_api_key(config_env)

    return env
