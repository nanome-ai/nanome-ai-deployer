# Nanome AI Deployment Scripts

## Infrastructure
- MARA server (Debian or Redhat based)
- Tool Server (Debian or Redhat based)
- Photon Server (Windows)


## Configuration
1) SSH into MARA Server<br>
```sh
ssh username@mara-server-host
```

2) Install git

*Redhat based system*
```sh
sudo yum update
sudo yum install git
```

*Debian based system*
```sh
sudo apt-get update
sudo apt install git
```

3) Clone install repo scripts
```sh
git clone https://github.com/nanome-ai/nanome-ai-deployer
```

4) Set up Python and pip

*Redhat based system*
```sh
sudo yum install python
curl -sS https://bootstrap.pypa.io/get-pip.py | python3
```

*Debian based system*
```sh
sudo apt install python
curl -sS https://bootstrap.pypa.io/get-pip.py | python3
```
5) Cd into nanome-ai-deployer directory
```sh
cd nanome-ai-deployer
```

6) Install Requirements
```sh
pip install -r requirements.txt
```

7) Run install scripts
```sh
python mara_setup.py
python photon_setup.py
```
