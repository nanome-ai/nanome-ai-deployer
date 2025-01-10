import os
from cli import utils, workspace
from setup_mara import setup_mara
from aws_login import login_to_aws

import enums


PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), 'playbooks')


def setup_nanome_ai():
    print(
        "\nThanks for using Nanome AI! Let's get started setting up your server!\n"
        "This script will set up the environment variables for 4 docker containers:\n"
        "\t- Workspace API: Acts as a data store of Nanome workspaces.\n"
        "\t- Workspace Load Service: Contains business logic for rendering structure files as a Nanome workspace.\n"
        "\t- Tool Server: Runs computations for MARA workflows.\n"
        "\t- MARA: Web Application and API for performing comp-chem workflows.\n"
    )
    input('Press ENTER to continue')
    host = input('What Domain name will you be using to access? (i.e. yourcompany.com) (Defaults to ip address)')
    if not host:
        host = utils.get_public_ip()


    https_info = utils.gather_https_info()
    protocol = 'https' if https_info['https_enabled'] else 'http'
    certs_path = https_info.get('certs_path', '')

    login_to_aws()

    print("Deploying Workspace API...")
    workspace_repo_host = f'workspace-repo-api.{host}'
    workspace_loader_host = f'workspace-service-api.{host}'

    repo_env = workspace.configure_workspace_api()
    repo_env['VIRTUAL_HOST'] = workspace_repo_host
    repo_env['LOAD_SERVICE'] = f'{workspace_loader_host}/load'
    utils.write_env_file(enums.WORKSPACE_REPO_ENV_FILE, repo_env)

    print("Deploying Workspace Load Service...")
    load_service_env = workspace.configure_workspace_load_service()
    load_service_env['VIRTUAL_HOST'] = workspace_loader_host
    load_service_env['NANOME_SERVICE_API_URL'] = f'{protocol}://{workspace_repo_host}'
    utils.write_env_file(enums.WORKSPACE_LOAD_SERVICE_ENV_FILE, load_service_env)

    # Run Setup MARA script
    mara_env, tool_server_env = setup_mara(
        host=host,
        protocol=protocol,
        certs_path=certs_path
    )

    mara_env_vars = {   
        'WORKSPACE_API_URL': f'{protocol}://{workspace_repo_host}',
        'NANOME_SERVICES_URL': f'{protocol}://{workspace_loader_host}',
    }
    utils.write_env_file(enums.MARA_ENV_FILE, mara_env_vars, append=True)

    # Return environment variables for each 
    return repo_env, load_service_env, mara_env, tool_server_env


if __name__ == "__main__":
    repo_env, loader_env, mara_env, tool_server_env = setup_nanome_ai()

    workspace_repo_host = repo_env['VIRTUAL_HOST']
    loader_repo_host = loader_env['VIRTUAL_HOST']
    mara_host = mara_env['VIRTUAL_HOST']
    tool_server_host = tool_server_env['VIRTUAL_HOST']
    print(
        "\nYour Services have been configured to run at the following urls\n"
        f"\t- MARA: {mara_host}\n"
        f"\t- Tool Server: {tool_server_host}\n"
        f"\t- Workspace API: {workspace_repo_host}\n"
        f"\t- Workspace Load Service: {loader_repo_host}\n"
        "\n To start the services, run `docker compose up -d`"
    )
