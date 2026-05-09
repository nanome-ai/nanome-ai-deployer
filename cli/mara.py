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
    """Force a ``provider:model`` string. Bare models on Anthropic/explicit OpenAI
    paths get prefixed; already-prefixed strings pass through."""
    if not model or ':' in model:
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
            'anthropic:claude-opus-4-7',
            'anthropic:claude-sonnet-4-6',
            'anthropic:claude-sonnet-4-6',
        ),
        provider_prefix='anthropic',
    )


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
    default_choice = {'api_key': 1, 'service_principal': 2, 'default': 3}.get(existing_mode, 1)
    auth_choice = ask_selection(
        'How should the container authenticate to Azure?',
        [
            'API key (LLM_API_KEY)',
            'Service Principal (tenant + client id + client secret)',
            'DefaultAzureCredential (AKS workload identity / Azure-hosted managed identity)',
        ],
        default=default_choice,
    )

    if auth_choice == '1':
        env['AZURE_AUTH_MODE'] = 'api_key'
    elif auth_choice == '2':
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
    else:
        env['AZURE_AUTH_MODE'] = 'default'
        env['AZURE_TOKEN_SCOPE'] = _prompt_with_default(
            'AZURE_TOKEN_SCOPE',
            mara_env.get('AZURE_TOKEN_SCOPE'),
            default='https://cognitiveservices.azure.com/.default',
        )
        print(
            "\nNote: DefaultAzureCredential only resolves on Azure-managed compute "
            "(AKS workload identity, Container Apps, App Service, VMs with managed "
            "identity) or when AZURE_* env vars are injected into the container. "
            "It will not work on plain Docker hosts off-Azure — use Service Principal there."
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
        prior_provider = 2
    elif prior_model.startswith('anthropic:'):
        prior_provider = 3
    else:
        prior_provider = 1

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
        ['OpenAI', 'Microsoft Azure (Foundry)', 'Anthropic'],
        default=prior_provider,
    )

    if llm_provider == '2':
        provider_env = configure_azure_envvars(existing_mara_env)
        env.update(provider_env)
        # Service principal / managed identity flows authenticate via Entra
        # tokens; no static API key is needed (or wanted) in that case.
        if provider_env.get('AZURE_AUTH_MODE') == 'api_key':
            env['LLM_API_KEY'] = _collect_llm_api_key(existing_mara_env)
    elif llm_provider == '3':
        env.update(configure_anthropic_envvars(existing_mara_env))
        env['LLM_API_KEY'] = _collect_llm_api_key(existing_mara_env)
    else:
        env.update(configure_openai_envvars(existing_mara_env))
        env['LLM_API_KEY'] = _collect_llm_api_key(existing_mara_env)

    return env
