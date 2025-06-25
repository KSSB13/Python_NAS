#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
# Your GitHub repository details
GITHUB_USERNAME="KSSB13"
REPO_NAME="Python_NAS"

# Name for the Docker image and container
DOCKER_IMAGE_NAME="python-nas"
DOCKER_CONTAINER_NAME="my-nas"

# --- Colors for output ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting Python NAS Installation...${NC}"

# --- Step 1: Install Prerequisites (Git & Docker) ---
echo -e "${YELLOW}---> Step 1: Updating system and installing prerequisites...${NC}"
# Update package lists
sudo apt-get update
# Install git to clone the repo
sudo apt-get install -y git curl

# Install Docker Engine if it's not already installed
if ! command -v docker &> /dev/null
then
    echo "Docker not found. Installing Docker..."
    # Use Docker's official convenience script
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    # Add the current user to the 'docker' group to run docker commands without sudo
    # This change requires a re-login to take effect.
    sudo usermod -aG docker $USER
    echo -e "${GREEN}Docker installed successfully.${NC}"
    echo -e "${YELLOW}NOTE: You may need to log out and log back in for Docker commands to work without 'sudo'.${NC}"
else
    echo -e "${GREEN}Docker is already installed.${NC}"
fi


# --- Step 2: Clone or Update the Repository ---
echo -e "${YELLOW}---> Step 2: Cloning project from GitHub...${NC}"
# If the directory already exists, pull the latest changes. Otherwise, clone it.
if [ -d "$REPO_NAME" ]; then
    echo "Repository already exists. Pulling latest changes..."
    cd $REPO_NAME
    git pull origin main
else
    git clone "https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
    cd $REPO_NAME
fi


# --- Step 3: Build the Docker Image ---
echo -e "${YELLOW}---> Step 3: Building the NAS Docker image...${NC}"
# Stop and remove the old container if it exists
if [ $(sudo docker ps -q -f name=$DOCKER_CONTAINER_NAME) ]; then
    echo "Stopping and removing old container..."
    sudo docker stop $DOCKER_CONTAINER_NAME
    sudo docker rm $DOCKER_CONTAINER_NAME
fi
sudo docker build -t $DOCKER_IMAGE_NAME .


# --- Step 4: Run the Docker Container ---
echo -e "${YELLOW}---> Step 4: Starting the NAS container...${NC}"
sudo docker run \
    -d \
    -p 8080:8080 \
    -v "$(pwd)/data":/app/data/files \
    -v "$(pwd)/instance":/app/instance \
    --name $DOCKER_CONTAINER_NAME \
    --restart always \
    $DOCKER_IMAGE_NAME

# --- Final Step: Show Success Message ---
echo ""
echo -e "${GREEN}---> Installation Complete! <---${NC}"
echo "Your Python NAS is now running in the background."
echo "To check the logs, run: ${YELLOW}sudo docker logs $DOCKER_CONTAINER_NAME${NC}"
echo "To stop the NAS, run: ${YELLOW}sudo docker stop $DOCKER_CONTAINER_NAME${NC}"
echo ""
# Get the IP address of the machine
IP_ADDRESS=$(hostname -I | awk '{print $1}')
echo "You can access your NAS from other devices on your network at:"
echo -e "${GREEN}http://$IP_ADDRESS:8080${NC}"
echo ""