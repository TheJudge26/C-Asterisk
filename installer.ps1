# Define repository details
$repoUrl = "https://github.com/TheJudge26/C-Asterisk-Alpha.git"
$destination = "C:\Program Files\CSTAR"

# Check for Administrator privileges

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Error "This script must be run as an Administrator."
    exit
}

# Check if Python is installed
try {
    $pythonVersion = python --version 2>$null
    Write-Host "Found $pythonVersion"
} catch {
    Write-Host "Python not found. Opening the official download page..."
    Start-Process "https://www.python.org/downloads/"
    exit
}

# 1. Ensure Pip is up to date (Crucial for finding the right llvmlite wheels)
Write-Host "Updating pip to ensure compatibility..."
python -m pip install --upgrade pip

# 2. Try to install dependencies
Write-Host "Installing C* dependencies. This may take a moment due to LLVM components..."
python -m pip install llvmlite

# 3. Verify the installation
$checkLLVM = python -c "import llvmlite; print('Success')" 2>$null
if ($checkLLVM -eq "Success") {
    Write-Host "llvmlite installed successfully!"
} else {
    Write-Error "llvmlite installation failed. You may need to install the Microsoft C++ Build Tools."
    exit
}
if (-not (Test-Path $destination)) {
    Write-Host "Cloning repository to $destination..."
    git clone $repoUrl $destination
} else {
    Write-Host "Destination already exists. Skipping clone."
}

# Add the folder to the System PATH environment variable
Write-Host "Adding $destination to PATH..."
$oldPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::Machine)

if ($oldPath -split ';' -notcontains $destination) {
    $newPath = "$oldPath;$destination"
    [Environment]::SetEnvironmentVariable("Path", $newPath, [EnvironmentVariableTarget]::Machine)
    Write-Host "Successfully added to PATH. Please restart your terminal for changes to take effect."
} else {
    Write-Host "Folder is already in PATH."
}
exit   
