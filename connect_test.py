import os
import winrm
import yaml

inventory_file = os.path.join(os.path.dirname(__file__), 'inventory.local.yaml')
inventory = yaml.safe_load(open(inventory_file))
windows_host = inventory['myhosts']['hosts']['windows']

username = windows_host['ansible_user']
pwd = windows_host['ansible_password']
host = windows_host['ansible_host']

session = winrm.Session(
    host,
    auth=(username, pwd),
    transport='ntlm',
    server_cert_validation='ignore',
)
# Run ipconfig in session
result = session.run_cmd('ipconfig')

