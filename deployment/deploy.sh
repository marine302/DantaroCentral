#!/bin/bash
# Dantaro Central Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="dantaro-central"
DEPLOY_USER="dantaro"
DEPLOY_PATH="/opt/dantaro-central"
VENV_PATH="${DEPLOY_PATH}/venv"
BACKEND_PATH="${DEPLOY_PATH}/backend"

echo -e "${GREEN}🚀 Starting Dantaro Central Deployment${NC}"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}❌ This script should not be run as root${NC}"
   exit 1
fi

# Function to print status
print_status() {
    echo -e "${YELLOW}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check system requirements
print_status "Checking system requirements..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi

# Check PostgreSQL
if ! command -v psql &> /dev/null; then
    print_status "PostgreSQL client not found. Installing..."
    sudo apt-get update
    sudo apt-get install -y postgresql-client
fi

# Check Redis
if ! command -v redis-cli &> /dev/null; then
    print_status "Redis client not found. Installing..."
    sudo apt-get install -y redis-tools
fi

print_success "System requirements check completed"

# Create deployment user if not exists
if ! id "$DEPLOY_USER" &>/dev/null; then
    print_status "Creating deployment user: $DEPLOY_USER"
    sudo useradd -m -s /bin/bash $DEPLOY_USER
    sudo usermod -aG sudo $DEPLOY_USER
    print_success "Deployment user created"
fi

# Create deployment directory
print_status "Setting up deployment directory..."
sudo mkdir -p $DEPLOY_PATH
sudo chown -R $DEPLOY_USER:$DEPLOY_USER $DEPLOY_PATH
print_success "Deployment directory ready"

# Copy project files
print_status "Copying project files..."
if [ -d "$BACKEND_PATH" ]; then
    sudo rm -rf $BACKEND_PATH
fi
sudo cp -r "$(pwd)/backend" $DEPLOY_PATH/
sudo cp -r "$(pwd)/deployment" $DEPLOY_PATH/
sudo chown -R $DEPLOY_USER:$DEPLOY_USER $DEPLOY_PATH
print_success "Project files copied"

# Create virtual environment
print_status "Setting up Python virtual environment..."
sudo -u $DEPLOY_USER python3 -m venv $VENV_PATH
sudo -u $DEPLOY_USER $VENV_PATH/bin/pip install --upgrade pip
sudo -u $DEPLOY_USER $VENV_PATH/bin/pip install -r $BACKEND_PATH/requirements.txt
print_success "Virtual environment ready"

# Setup environment file
print_status "Setting up environment configuration..."
if [ ! -f "$DEPLOY_PATH/.env" ]; then
    sudo cp $DEPLOY_PATH/deployment/.env.production $DEPLOY_PATH/.env
    sudo chown $DEPLOY_USER:$DEPLOY_USER $DEPLOY_PATH/.env
    print_status "Please edit $DEPLOY_PATH/.env with your configuration"
fi

# Database setup
print_status "Setting up database..."
cd $BACKEND_PATH
sudo -u $DEPLOY_USER $VENV_PATH/bin/python migrate.py migrate
print_success "Database migration completed"

# Install systemd services
print_status "Installing systemd services..."
sudo cp $DEPLOY_PATH/deployment/systemd/dantaro-worker.service /etc/systemd/system/
sudo cp $DEPLOY_PATH/deployment/systemd/dantaro-api.service /etc/systemd/system/
sudo systemctl daemon-reload
print_success "Systemd services installed"

# Enable and start services
print_status "Starting services..."
sudo systemctl enable dantaro-worker
sudo systemctl enable dantaro-api
sudo systemctl start dantaro-worker
sudo systemctl start dantaro-api
print_success "Services started"

# Check service status
print_status "Checking service status..."
sleep 5

if sudo systemctl is-active --quiet dantaro-worker; then
    print_success "Worker service is running"
else
    print_error "Worker service failed to start"
    sudo systemctl status dantaro-worker
fi

if sudo systemctl is-active --quiet dantaro-api; then
    print_success "API service is running"
else
    print_error "API service failed to start"
    sudo systemctl status dantaro-api
fi

print_success "🎉 Dantaro Central deployment completed!"
echo ""
echo -e "${GREEN}📊 Service Information:${NC}"
echo "  API Server: http://localhost:8000"
echo "  Health Check: http://localhost:8000/health"
echo "  API Documentation: http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}📋 Useful Commands:${NC}"
echo "  Check status: sudo systemctl status dantaro-worker dantaro-api"
echo "  View logs: sudo journalctl -u dantaro-worker -f"
echo "  Restart services: sudo systemctl restart dantaro-worker dantaro-api"
echo ""
echo -e "${YELLOW}⚠️  Remember to:${NC}"
echo "  1. Configure $DEPLOY_PATH/.env with your API keys"
echo "  2. Set up PostgreSQL and Redis if not using Docker"
echo "  3. Configure firewall rules for port 8000"
