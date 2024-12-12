# Nanome AI Deployment Scripts

## Infrastructure
- MARA server (Debian or Redhat based)
- Photon Server (Windows)


## Configuration
1) SSH into MARA Server<br>
```sh
ssh username@mara-server-host
```

2) Install git

```sh
# Redhat based system
sudo yum update
sudo yum install git
```

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
# Redhat based system
sudo yum install python
curl -sS https://bootstrap.pypa.io/get-pip.py | python3
```

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
python setup_mara.py
python setup_windows_server.py
```
