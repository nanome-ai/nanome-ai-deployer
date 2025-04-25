import os
from cli import utils, workspace
from setup_mara import setup_mara
from aws_login import login_to_aws

import enums


PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), 'playbooks')


def setup_nanome_ai():
    print(
        "\nThanks for using Nanome AI! Let's get started setting up your server!\n\n"
        "This script will set up the environment variables for 6 docker containers:\n"
        " - Workspace API: The main API for Nanome v2 workspaces.\n"
        " - Workspace DB: The database for the workspace API.\n"
        " - MARA: Web Application and API for performing comp-chem workflows.\n"
        " - MARA Tool Server: Runs computations for MARA workflows.\n"
        " - MARA Embeddings: Vector database for storing embeddings.\n"
        " - Nanome auth proxy: Proxy for Nanome authentication used by VR headsets.\n"
    )
    input('Press ENTER to continue')
    host = input('What Domain name will you be using to access? (i.e. yourcompany.com) (Defaults to ip address)')
    if not host:
        host = utils.get_public_ip() + '.nip.io'


    https_info = utils.gather_https_info()
    protocol = 'https' if https_info['https_enabled'] else 'http'
    certs_path = https_info.get('certs_path', '')

    login_to_aws()

    print("Deploying Workspace API...")
    workspaces_host = f'workspaces.{host}'

    workspaces_env = workspace.configure_workspace_api()
    workspaces_env['VIRTUAL_HOST'] = workspaces_host
    utils.write_env_file(enums.WORKSPACES_ENV_FILE, workspaces_env)

    nanome_auth_proxy_host = f'nanome-auth.{host}'
    utils.write_env_file(enums.AUTH_PROXY_ENV_FILE, {'VIRTUAL_HOST': nanome_auth_proxy_host})

    # Run Setup MARA script
    mara_env, tool_server_env = setup_mara(
        host=host,
        protocol=protocol,
        certs_path=certs_path
    )

    mara_env_vars = {
        'WORKSPACE_API_URL': f'{protocol}://{workspaces_host}',
    }
    utils.write_env_file(enums.MARA_ENV_FILE, mara_env_vars, append=True)

    # Return environment variables for each
    return workspaces_env, mara_env, tool_server_env


if __name__ == "__main__":
    workspaces_env, mara_env, tool_server_env = setup_nanome_ai()

    workspaces_host = workspaces_env['VIRTUAL_HOST']
    mara_host = mara_env['VIRTUAL_HOST']
    tool_server_host = tool_server_env['VIRTUAL_HOST']
    print(
        "\nYour Services have been configured to run at the following urls\n"
        f"\t- MARA: {mara_host}\n"
        f"\t- Tool Server: {tool_server_host}\n"
        f"\t- Workspace API: {workspaces_host}\n"
        "\n To start the services, run `docker compose up -d`"
    )
