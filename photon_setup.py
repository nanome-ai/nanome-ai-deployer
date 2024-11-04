import os
import yaml
import subprocess

'''
On MacOS, If you receive this error:
objc[9034]: +[NSString initialize] may have been in progress in another thread when fork() was called. We cannot safely call it or ignore it in the fork() child process. Crashing instead. Set a breakpoint on objc_initializeAfterForkError to debug.
ERROR! A worker was found in a dead state

You can try to set the following environment variable:
export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
'''


PLAYBOOKS_DIR = os.path.join(os.path.dirname(__file__), 'playbooks')


def gather_windows_host_info():
    # Get ip address of remote server
    ip_address = input("Enter the server IP address: ")
    port = input("Enter the port number for WinRM HTTP connection (default is 5985): ") or '5985'
    # Ask for the username to log into the server
    username = input("Enter the username for RDP login: ")
    # Ask for the path to the private key file
    password = input("Enter your authentication password: ")
    host_config = {
        'ansible_host': ip_address,
        'ansible_port': port,
        'ansible_user': username,
        'ansible_password': password,
        'ansible_connection': 'winrm',
        'ansible_winrm_scheme': 'http',
        'ansible_winrm_transport': 'ntlm',
        'ansible_winrm_server_cert_validation': 'ignore',
    }
    return host_config


def main():
    print("\nLet's set up your Photon Server!\n")
    inventory_filepath = os.path.join(os.path.dirname(__file__), 'inventory.local.yaml')
    # Determine if we need to ask for windows server configurations
    server_config_actions = None
    if os.path.exists(inventory_filepath):
        inventory_data = yaml.safe_load(open(inventory_filepath))
        windows_host = inventory_data.get('myhosts', {}).get('hosts', {}).get('windows', {}) 
        if not windows_host:
            server_config_actions = '2'    

        while server_config_actions not in ['1', '2']:
            server_config_actions = input((
                f"You already have a windows server configured in {inventory_filepath}.\n"
                "How do you want to proceed?\n"
                "1. Use existing settings\n"
                "2. Update server configurations\n\n"
                "Make a selection (1|2): "
            ))
    update_server_configs = server_config_actions == '2'
    if update_server_configs:
        windows_inventory = gather_windows_host_info()
        inventory_data['myhosts']['hosts']['windows'] = windows_inventory
        with open(inventory_filepath, 'w') as f:
            yaml.dump(inventory_data, f)

    # Run Ansible Playbook
    playbook_path = os.path.join(PLAYBOOKS_DIR, 'install_photon.yaml')
    cmd = [
        'ansible-playbook',
        playbook_path,
        '-i', inventory_filepath,
        '-vvv',
    ]
    subprocess.run(cmd)


if __name__ == '__main__':
    main()
