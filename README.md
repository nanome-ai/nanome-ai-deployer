# Nanome AI Deployment Scripts

## Infrastructure

- MARA server (Ubuntu)
- Photon Server (Windows)

## Deployment

### Setup

Log in to the server via SSH and run the following commands
(step-by-step explanation in next section)

```sh
sudo apt-get update
sudo apt install -y git python3 python3-venv
git clone https://github.com/nanome-ai/nanome-ai-deployer
cd nanome-ai-deployer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python install_prereqs.py
sudo reboot
```

After reboot
```sh
cd nanome-ai-deployer
source venv/bin/activate
python setup_nanome.py
docker compose up -d
```

### Update / Redeploy

```sh
cd nanome-ai-deployer
python aws_login.py
docker compose up -d
```

### Setup Step-by-step

1) Install git and python
   ```sh
   sudo apt-get update
   sudo apt install -y git python3 python3-venv
   ```

2) Clone this repository
   ```sh
   git clone https://github.com/nanome-ai/nanome-ai-deployer
   cd nanome-ai-deployer
   ```

3) Set up Python and pip
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```

4) Install script dependencies, Docker, and AWSCLI
   ```sh
   pip install -r requirements.txt
   python install_prereqs.py
   ```

5) Reboot the server
   ```sh
   sudo reboot
   ```

6) Reactivate virtualenv
   ```sh
   cd nanome-ai-deployer
   source venv/bin/activate
   ```

7)  Run setup script and start services
    ```sh
    python setup_nanome.py
    docker compose up -d
    ```

### Troubleshooting

- **"An error occurred (InvalidClientTokenId) when calling the GetCallerIdentity operation" during setup**
  The AWS credentials were likely entered incorrectly. You'll have the opportunity to reenter them when you run `setup_nanome.py`. Alternatively, you can edit them directly by opening `~/.aws/credentials` in a text editor.

- **"Address already in use" error when starting services**
  Another program on the server is already using port 80. To find out what it is, run:
  ```sh
  sudo lsof -i :80
  ```
  If the program is nginx (a web server sometimes included in the base VM image), you can remove it and restart:
  ```sh
  sudo apt remove nginx nginx-common
  docker compose down
  docker compose up -d
  ```

- **MARA returns a "certificate verify failed" error when running some tools like Download from RCSB**
  Your network may be using SSL introspection, which interferes with outbound requests. Contact your IT team to request an exemption, or reach out to Nanome support for a list of domains that need to be whitelisted (e.g. rcsb.org).

- **Web UI shows "Failed to fetch" or you cannot create a workspace**
  The Workspace API service may not be running. Check its logs for errors:
  ```sh
  docker compose logs workspace-api
  ```
  Also verify that the URL in your `.env.workspaces` file is correct.

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
