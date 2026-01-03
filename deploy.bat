@echo off
REM Remote Camera System - Windows Deployment Script

echo 🚀 Remote Camera System - Windows Deployment
echo ===========================================

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ Running as administrator
) else (
    echo ❌ Please run as administrator
    pause
    exit /b 1
)

REM Install Python dependencies
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

REM Create logs directory
if not exist "logs" mkdir logs

REM Create Windows service script
echo ⚙️ Creating Windows service script...
(
echo @echo off
echo cd /d "%~dp0"
echo "venv\Scripts\python.exe" app.py
) > service.bat

REM Create startup script
echo 📜 Creating startup script...
(
echo @echo off
echo cd /d "%~dp0"
echo call venv\Scripts\activate.bat
echo set PORT=5000
echo python app.py
) > start.bat

REM Configure Windows Firewall
echo 🔥 Configuring Windows Firewall...
netsh advfirewall firewall add rule name="Remote Camera" dir=in action=allow protocol=TCP localport=5000

REM Get local IP
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do set LOCAL_IP=%%a
set LOCAL_IP=%LOCAL_IP: =%

echo ✅ Deployment complete!
echo ===========================================
echo 🌐 Local IP: %LOCAL_IP%
echo 📱 Access URL: http://%LOCAL_IP%:5000
echo 👤 Admin Panel: http://%LOCAL_IP%:5000
echo ===========================================
echo 📋 Commands:
echo   Start: start.bat
echo   Stop: Close the terminal or Ctrl+C
echo ===========================================

echo 🎉 Remote Camera System deployed successfully!
echo 📱 Open http://%LOCAL_IP%:5000 in your browser

pause
