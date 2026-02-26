import os
from cli import utils, workspace
from setup_mara import setup_mara
from aws_login import login_to_aws

import enums


PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), 'playbooks')


def setup_nanome_ai():
    # Read existing env files to prefill defaults on re-run
    existing_mara_env = utils.read_env_file(enums.MARA_ENV_FILE)
    default_host = utils.extract_host_from_env(existing_mara_env, 'nanome')

    print(
        "\nThanks for using Nanome! Let's get started setting up your server!\n\n"
        "This script will set up the environment variables for 6 docker containers:\n"
        " - Workspace API: The main API for Nanome v2 workspaces.\n"
        " - Workspace DB: The database for the workspace API.\n"
        " - Web UI: Web Application and API for managing workspaces and performing comp-chem workflows.\n"
        " - Tool Server: Runs computations for MARA workflows.\n"
        " - Embeddings: Vector database for storing embeddings.\n"
        " - Nanome auth proxy: Proxy for Nanome authentication used by VR headsets.\n"
    )
    input('Press ENTER to continue')
    host = utils.gather_host_info(default=default_host)

    cert_type = utils.gather_https_info(host)
    protocol = 'http' if cert_type == 'None' else 'https'

    workspaces_host = f'workspaces.{host}'
    workspaces_env = workspace.configure_workspace_api()
    workspaces_env['VIRTUAL_HOST'] = workspaces_host
    if cert_type == 'Default':
        workspaces_env['CERT_NAME'] = 'default'
    elif cert_type == 'Individual':
        workspaces_env['CERT_NAME'] = 'workspaces'
    utils.write_env_file(enums.WORKSPACES_ENV_FILE, workspaces_env)

    nanome_auth_env = {'VIRTUAL_HOST': f'nanome-auth.{host}'}
    if cert_type == 'Default':
        nanome_auth_env['CERT_NAME'] = 'default'
    elif cert_type == 'Individual':
        nanome_auth_env['CERT_NAME'] = 'nanome-auth'
    utils.write_env_file(enums.AUTH_PROXY_ENV_FILE, nanome_auth_env)

    # Run Setup MARA script
    mara_env, tool_server_env = setup_mara(host=host, cert_type=cert_type)

    mara_env_vars = {
        'WORKSPACE_API_URL': f'{protocol}://{workspaces_host}',
    }
    utils.write_env_file(enums.MARA_ENV_FILE, mara_env_vars, append=True)

    # Return environment variables for each
    return workspaces_env, mara_env, tool_server_env, nanome_auth_env


if __name__ == "__main__":
    try:
        workspaces_env, mara_env, tool_server_env, nanome_auth_env = setup_nanome_ai()
        login_to_aws()

        workspaces_host = workspaces_env['VIRTUAL_HOST']
        mara_host = mara_env['VIRTUAL_HOST']
        tool_server_host = tool_server_env['VIRTUAL_HOST']
        auth_proxy_host = nanome_auth_env['VIRTUAL_HOST']
        print(
            "\nYour services have been configured to run at the following urls\n"
            f" - Web UI: {mara_host}\n"
            f" - Tool Server: {tool_server_host}\n"
            f" - Workspace API: {workspaces_host}\n"
            f" - Nanome Auth Proxy: {auth_proxy_host}\n"
            "\nTo start the services, run `docker compose up -d`"
        )
    except KeyboardInterrupt:
        print("\nSetup cancelled")
