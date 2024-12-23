import os
import subprocess
from .utils import PLAYBOOKS_DIR

def configure_workspace_api(inventory_filepath):
    deploy_workspace_api_playbook = os.path.join(PLAYBOOKS_DIR, 'deploy_workspace_api.yaml')
    subprocess.run([
        'ansible-playbook',
        '-i', inventory_filepath,
        deploy_workspace_api_playbook
    ])

def configure_workspace_load_service(inventory_filepath):
    deploy_workspace_load_service_playbook = os.path.join(PLAYBOOKS_DIR, 'deploy_workspace_load_service.yaml')
    subprocess.run([
        'ansible-playbook',
        '-i', inventory_filepath,
        deploy_workspace_load_service_playbook
    ])