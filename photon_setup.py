import os
import subprocess


PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), 'playbooks')
inventory_filepath = os.path.join(os.path.dirname(__file__), 'inventory.local.yaml')


# Run Ansible Playbook
playbook_path = os.path.join(PLAYBOOKS_DIR, 'install_photon.yaml')
cmd = [
    'ansible-playbook',
    playbook_path,
    '-i', inventory_filepath,
    '-vvv',
]
subprocess.run(cmd)
