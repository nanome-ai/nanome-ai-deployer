import subprocess

def login_to_aws():
    print("\n\nLogging into AWS ECR... ", end='', flush=True)
    cmd = (
            'aws ecr get-login-password --region us-west-1 '
            '| docker login --username AWS --password-stdin 441665557124.dkr.ecr.us-west-1.amazonaws.com'
        )
    subprocess.run(cmd, shell=True)

if __name__ == '__main__':
    login_to_aws()
