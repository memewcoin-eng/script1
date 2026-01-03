#!/bin/bash
# Remote Camera System - VPS Deployment Script

echo "🚀 Remote Camera System - VPS Deployment"
echo "=========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
apt update && apt upgrade -y

# Install system dependencies
echo "🐍 Installing Python and dependencies..."
apt install -y python3 python3-pip python3-venv git curl build-essential cmake pkg-config libjpeg-dev libtiff5-dev libpng-dev libavcodec-dev libavformat-dev libswscale-dev libv4l-dev libxvidcore-dev libx264-dev libgtk-3-dev libatlas-base-dev gfortran

# Install Node.js (for SocketIO compatibility)
echo "📦 Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt-get install -y nodejs

# Create application directory
echo "📁 Creating application directory..."
mkdir -p /opt/remote-camera
cd /opt/remote-camera

# Copy files (assuming they're in the same directory)
echo "📋 Copying application files..."
cp -r ./* /opt/remote-camera/

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Add user bin to PATH
echo "🔧 Adding user bin to PATH..."
echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
source ~/.bashrc

# Create systemd service
echo "⚙️ Creating systemd service..."
cat > /etc/systemd/system/remote-camera.service << EOF
[Unit]
Description=Remote Camera System
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/remote-camera
Environment=PATH=/opt/remote-camera/venv/bin
Environment=PORT=5000
ExecStart=/opt/remote-camera/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Configure firewall
echo "🔥 Configuring firewall..."
ufw allow 5000/tcp
ufw allow 22/tcp
ufw --force enable

# Create startup script
echo "📜 Creating startup script..."
cat > /opt/remote-camera/start.sh << EOF
#!/bin/bash
cd /opt/remote-camera
source venv/bin/activate
export PORT=5000
python app.py
EOF

chmod +x /opt/remote-camera/start.sh

# Enable and start service
echo "🚀 Enabling and starting service..."
systemctl daemon-reload
systemctl enable remote-camera
systemctl start remote-camera

# Check service status
echo "📊 Checking service status..."
sleep 5
systemctl status remote-camera

# Get server IP
echo "🌐 Getting server IP..."
SERVER_IP=$(curl -s ifconfig.me)
echo "✅ Deployment complete!"
echo "=========================================="
echo "🌐 Server IP: $SERVER_IP"
echo "📱 Access URL: http://$SERVER_IP:5000"
echo "👤 Admin Panel: http://$SERVER_IP:5000"
echo "=========================================="
echo "📋 Commands:"
echo "  Start service: systemctl start remote-camera"
echo "  Stop service: systemctl stop remote-camera"
echo "  Restart service: systemctl restart remote-camera"
echo "  Check status: systemctl status remote-camera"
echo "  View logs: journalctl -u remote-camera -f"
echo "=========================================="

# Create log directory
mkdir -p /opt/remote-camera/logs

echo "🎉 Remote Camera System deployed successfully!"
echo "📱 Open http://$SERVER_IP:5000 in your browser"
