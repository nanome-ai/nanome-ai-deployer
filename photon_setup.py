import os
import subprocess

'''
On MacOS, If you receive this error:
objc[9034]: +[NSString initialize] may have been in progress in another thread when fork() was called. We cannot safely call it or ignore it in the fork() child process. Crashing instead. Set a breakpoint on objc_initializeAfterForkError to debug.
ERROR! A worker was found in a dead state

You can try to set the following environment variable:
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
'''

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
