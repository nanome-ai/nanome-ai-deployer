# Nanome AI Deployment Scripts

## Infrastructure

- MARA server (Ubuntu)
- Photon Server (Windows)

## Configuring MARA Server

1) SSH into MARA Server

```sh
ssh username@mara-server-host
```

2) Install git

```sh
# Debian based system
sudo apt-get update
sudo apt install git
```

3) Clone install repo scripts
```sh
git clone https://github.com/nanome-ai/nanome-ai-deployer
```


4) Cd into nanome-ai-deployer directory
```sh
cd nanome-ai-deployer
```

5) Set up Python and pip

```sh
# Debian based system
sudo apt install python3

# Set up virtualenv
sudo apt install python3-venv
python3 -m venv venv
source venv/bin/activate
```

6) Install Requirements
```sh
pip install -r requirements.txt
```

7) Install Docker and AWSCLI
```sh
python install_prereqs.py
```

8) Reboot you MARA server, so that Docker changes take effect.

9) Run install scripts
```sh
# MARA only deployments
python setup_mara.py
```
OR
```sh
# Nanome AI deployment
python setup_nanome_ai.py
```

## Configuring Windows Server

This Repo contains a Powershell script `configure_windows.ps1` for downloading and installing Photon on the Windows Server

1) Connect to your Windows server via RDP

2) Copy `configure_windows.ps1` onto the Desktop of your Windows Server. This is currently a manual process, you may have to create a new file, and copy contents directly.

3) In Powershell, run the script. It will ask you for the AWS credentials provided to you by Nanome

```sh
cd Desktop
./configure_windows.ps1
```

4) Once the script has completed, open the Photon Control Panel, and start service. (To be documented later)
