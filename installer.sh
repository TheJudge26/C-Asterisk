echo "THis is the installer script written in shell for linux!"
echo "This script will install the necessary dependencies and set up the environment for the project."
echo "Please make sure you have the necessary permissions to run this script."
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root"
  exit
fi
if $(apt-get update) && (apt-get install -y python3 python3-pip) && (pip3 install llvmlite); then
  echo "Dependencies installed successfully!"
else
  echo "Failed to install dependencies. Please check the error messages above."
  exit 1
fi
echo "Environment set up successfully!"
if $(git clone https://github.com/TheJudge26/C-Asterisk-Alpha.git) ; then
  mv C-Asterisk-Alpha usr/bin/CSTAR/
  mv usr/bin/CSTAR/cstar usr/bin/
  cd usr/bin/CSTAR/
  chmod +x cstar
  echo "Project files set up successfully!"
else
  echo "Failed to clone the repository. Please check the error messages above."
  exit 1
fi
echo "Installation completed successfully! You can now run the project using 'cstar' command."
