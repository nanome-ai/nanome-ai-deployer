function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::Machine)
}

function Install-Python {
    Write-Host "Installing Python"
    # Variables
    $pythonInstallerUrl = "https://www.python.org/ftp/python/3.11.6/python-3.11.6-amd64.exe"
    $installerPath = "C:\Users\Administrator\Desktop\python-installer.exe"

    # Function to check if Python is installed
    function Check-Python {
        try {
            $pythonVersion = python --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Output $pythonVersion
                return $true
            } else {
                return $false
            }
        } catch {
            return $false
        }
    }

    # Check if Python is installed
    if (-not (Check-Python)) {
        Write-Host "Python not found. Proceeding with installation..."

        # Download Python installer
        Write-Host "Downloading Python installer..."
        Invoke-WebRequest -Uri $pythonInstallerUrl -OutFile $installerPath

        # Install Python
        Write-Host "Installing Python..."
        Start-Process -FilePath $installerPath -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait

        # Verify Python installation
        Refresh-Path
        if (Check-Python) {
            $installedVersion = python --version
            Write-Host "Python installed successfully. Version: $installedVersion"
        } else {
            Write-Host "Python installation failed."
        }
    } else {
        $installedVersion = python --version
        Write-Host "Python is already installed. Version: $installedVersion"
    }

}


function Install-AWSCLI {
    Write-Host "Checking if AWS CLI is already installed..."
    try {
        $awsVersion = aws --version
        Write-Host "AWS CLI is already installed: $awsVersion"
        return
    } catch {
        Write-Host "AWS CLI is not installed. Proceeding with installation..."
    }

    $awsCliInstallerUrl = "https://awscli.amazonaws.com/AWSCLIV2.msi"
    $awsCliInstallerPath = "$env:USERPROFILE\Downloads\AWSCLIV2.msi"

    Write-Host "Downloading AWS CLI installer..."
    Invoke-WebRequest -Uri $awsCliInstallerUrl -OutFile $awsCliInstallerPath -ErrorAction Stop

    if (-Not (Test-Path -Path $awsCliInstallerPath)) {
        Write-Error "Failed to download AWS CLI installer."
        exit 1
    }

    Write-Host "Installing AWS CLI..."
    Start-Process -FilePath "msiexec.exe" -ArgumentList "/i $awsCliInstallerPath /quiet" -Wait -NoNewWindow

    Refresh-Path
    Write-Host "Verifying AWS CLI installation..."
    try {
        $awsVersion = aws --version
        Write-Host "AWS CLI installed successfully: $awsVersion"
    } catch {
        Write-Error "AWS CLI installation verification failed. Please check the installation."
        exit 1
    }

    Write-Host "AWS CLI installation completed successfully."
}


function Configure-Photon {
    $photonS3 = "s3://nanome/enterprise_deployment/Photon-OnPremise-Server-SDK_v4-0-29-11263.zip"
    $licenseS3 = "https://nanome.s3.us-west-1.amazonaws.com/enterprise_deployment/simim91296%40gocasin.com.Photon-vX.free.100-ccu.license"
    $photonZipDir = "C:\Users\Administrator\Desktop\photon.zip"
    $photonDir = "C:\Users\Administrator\Desktop\photon"
    $licenseFile = "C:\Users\Administrator\Desktop\photon\deploy\bin_Win64\photon.license"
    $photonBinDir = "C:\Users\Administrator\Desktop\photon\Photon-OnPremise-Server-SDK_v4-0-29-11263\deploy\bin_Win64"

    if (-Not (Test-Path -Path $photonZipDir)) {
        Write-Host "Photon zip file not found. Downloading from S3..."
        
        aws s3 cp $photonS3 $photonZipDir
        if (-Not $? -or -Not (Test-Path -Path $photonZipDir)) {
            Write-Error "Failed to download Photon zip file from S3."
            exit 1
        }

        Write-Host "Unzipping Photon package..."
        Expand-Archive -Path $photonZipDir -DestinationPath $photonDir -Force
        if (-Not $? -or -Not (Test-Path -Path $photonDir)) {
            Write-Error "Failed to unzip Photon package."
            exit 1
        }
    } else {
        Write-Host "Photon zip file already exists. Skipping download and extraction."
    }
}

# Main script execution
Install-Python
Install-AWSCLI
aws configure
Configure-Photon
