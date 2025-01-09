import getpass
import os
import subprocess

from cli import utils, mara, workspace
from aws_login import login_to_aws
import enums

PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), 'playbooks')


def write_env_file(env_filepath, env_dict: dict) -> None:
    with open(env_filepath, 'w') as f:
        for key, value in env_dict.items():
            line = f'{key}={value}\n'
            f.write(line)


def main():
    print(
        "\nThanks for using Nanome AI! Let's get started setting up your server!\n"
        "This script will set up the environment variables for 4 docker containers:\n"
        "\t- Workspace API: Acts as a data store of Nanome workspaces.\n"
        "\t- Workspace Load Service: Contains business logic for rendering structure files as a Nanome workspace.\n"
        "\t- Tool Server: Runs computations for MARA workflows.\n"
        "\t- MARA: Web Application and API for performing comp-chem workflows.\n"
    )
    input('Press ENTER to continue')

    host = input('What Domain name will you be using to access? (ex. yourcompany.com) (Defaults to ip address ')
    breakpoint()

    login_to_aws()

    print("Deploying Workspace API...")
    workspace_repo_host = f'workspace-repo-api.{host}'

    repo_env = workspace.configure_workspace_api()
    repo_env['VIRTUAL_HOST'] = workspace_repo_host
    write_env_file(enums.WORKSPACE_REPO_ENV_FILE, repo_env)

    print("Deploying Workspace Load Service...")
    loader_repo_host = f'workspace-service-api.{host}'
    load_service_env = workspace.configure_workspace_load_service()
    load_service_env['VIRTUAL_HOST'] = loader_repo_host
    write_env_file(enums.WORKSPACE_LOAD_SERVICE_ENV_FILE, load_service_env)

    # Setup tool-server .env file
    print("\nCollecting Tool Server Values...\n")
    tool_server_host = f'mara-tools.{host}'
    tool_server_env_file = enums.TOOL_SERVER_ENV_FILE
    existing_tool_server_env = utils.read_env_file(tool_server_env_file)
    tool_server_env = mara.configure_tool_server(existing_tool_server_env)
    tool_server_env['VIRTUAL_HOST'] = tool_server_host
    write_env_file(tool_server_env_file, tool_server_env)

    # Configure the mara .env file
    tool_server_api_key = tool_server_env.get('API_KEY', None)
    print('\nConfiguring the MARA Server...\n')
    mara_env_file = enums.MARA_ENV_FILE
    existing_mara_env = utils.read_env_file(mara_env_file)
    mara_env = mara.configure_mara_server(existing_mara_env, tool_server_api_key)
    mara_env['TOOL_SERVER_KEY'] = tool_server_api_key
    mara_host = f'mara.{host}'
    mara_env['VIRTUAL_HOST'] = mara_host
    write_env_file(mara_env_file, mara_env)

    print(
        "\nYour Services have been configured to run at the following urls\n"
        f"\t- MARA: {mara_host}\n"
        f"\t- Tool Server: {tool_server_host}\n"
        f"\t- Workspace API: {workspace_repo_host}\n"
        f"\t- Workspace Load Service: {loader_repo_host}\n"
        "\n To start the services, run `docker compose up -d"
    )

if __name__ == "__main__":
    main()
