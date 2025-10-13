import socket
import threading
import time
from datetime import datetime
import json
from flask import Flask, render_template, request, jsonify
import webview
import sys
import os
import queue

class ChatServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.clients = []
        self.server_socket = None
        self.running = False
        
    def start_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            self.running = True
            print(f"服务器启动在 {self.host}:{self.port}")
            
            # 启动接受客户端连接的线程
            accept_thread = threading.Thread(target=self.accept_clients)
            accept_thread.daemon = True
            accept_thread.start()
            return True
        except Exception as e:
            print(f"服务器启动失败: {e}")
            return False
    
    def accept_clients(self):
        while self.running:
            try:
                client_socket, client_address = self.server_socket.accept()
                print(f"新客户端连接: {client_address}")
                
                # 为每个客户端创建单独的线程
                client_thread = threading.Thread(
                    target=self.handle_client, 
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()
                
                self.clients.append((client_socket, client_address))
                
            except Exception as e:
                if self.running:
                    print(f"接受客户端连接错误: {e}")
    
    def handle_client(self, client_socket, client_address):
        while self.running:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                    
                # 解析消息
                try:
                    message_data = json.loads(message)
                    username = message_data.get('username', '未知用户')
                    content = message_data.get('content', '')
                    
                    # 创建格式化消息
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    formatted_message = f"{client_address[0]} | {timestamp} | {username}: {content}"
                    
                    print(f"收到消息: {formatted_message}")
                    
                    # 广播给所有客户端
                    self.broadcast_message({
                        'type': 'message',
                        'content': formatted_message,
                        'timestamp': timestamp,
                        'ip': client_address[0],
                        'username': username
                    })
                    
                except json.JSONDecodeError:
                    print(f"消息格式错误: {message}")
                    
            except Exception as e:
                print(f"处理客户端消息错误: {e}")
                break
        
        # 客户端断开连接
        self.remove_client(client_socket, client_address)
        client_socket.close()
    
    def broadcast_message(self, message_data):
        message_json = json.dumps(message_data)
        disconnected_clients = []
        
        for client_socket, client_address in self.clients:
            try:
                client_socket.send(message_json.encode('utf-8'))
            except Exception as e:
                print(f"发送消息到 {client_address} 失败: {e}")
                disconnected_clients.append((client_socket, client_address))
        
        # 移除断开的客户端
        for client in disconnected_clients:
            self.remove_client(*client)
    
    def remove_client(self, client_socket, client_address):
        if (client_socket, client_address) in self.clients:
            self.clients.remove((client_socket, client_address))
            print(f"客户端断开连接: {client_address}")
            
            # 广播用户离开消息
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            leave_message = f"{client_address[0]} | {timestamp} | 用户离开聊天室"
            self.broadcast_message({
                'type': 'system',
                'content': leave_message,
                'timestamp': timestamp
            })
    
    def stop_server(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        for client_socket, _ in self.clients:
            client_socket.close()
        self.clients.clear()
        print("服务器已停止")

class ChatClient:
    def __init__(self, host='localhost', port=8080, username='用户'):
        self.host = host
        self.port = port
        self.username = username
        self.client_socket = None
        self.connected = False
        self.message_queue = queue.Queue()  # 添加消息队列
        self.last_message_id = 0
        
    def connect(self):
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((self.host, self.port))
            self.connected = True
            
            # 启动接收消息的线程
            receive_thread = threading.Thread(target=self.receive_messages)
            receive_thread.daemon = True
            receive_thread.start()
            
            return True
        except Exception as e:
            print(f"连接服务器失败: {e}")
            return False
    
    def send_message(self, content):
        if self.connected:
            try:
                message_data = {
                    'username': self.username,
                    'content': content
                }
                self.client_socket.send(json.dumps(message_data).encode('utf-8'))
                return True
            except Exception as e:
                print(f"发送消息失败: {e}")
                self.connected = False
                return False
        return False
    
    def receive_messages(self):
        while self.connected:
            try:
                message = self.client_socket.recv(1024).decode('utf-8')
                if not message:
                    break
                    
                try:
                    message_data = json.loads(message)
                    # 将消息添加到队列
                    self.last_message_id += 1
                    message_data['id'] = self.last_message_id
                    self.message_queue.put(message_data)
                except json.JSONDecodeError:
                    print(f"接收到的消息格式错误: {message}")
                        
            except Exception as e:
                if self.connected:
                    print(f"接收消息错误: {e}")
                break
        
        self.connected = False
        # 添加断开连接消息
        self.message_queue.put({
            'type': 'error',
            'content': '与服务器断开连接',
            'id': self.last_message_id + 1
        })
    
    def get_new_messages(self, last_id=0):
        """获取自last_id之后的新消息"""
        messages = []
        while not self.message_queue.empty():
            try:
                message = self.message_queue.get_nowait()
                if message['id'] > last_id:
                    messages.append(message)
            except queue.Empty:
                break
        return messages
    
    def disconnect(self):
        self.connected = False
        if self.client_socket:
            self.client_socket.close()

# Flask应用
app = Flask(__name__)
chat_server = None
chat_client = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_server', methods=['POST'])
def start_server():
    global chat_server
    data = request.json
    port = int(data.get('port', 8080))
    
    if chat_server and chat_server.running:
        return jsonify({'success': False, 'message': '服务器已在运行'})
    
    chat_server = ChatServer(port=port)
    if chat_server.start_server():
        return jsonify({'success': True, 'message': f'服务器启动成功，端口: {port}'})
    else:
        return jsonify({'success': False, 'message': '服务器启动失败'})

@app.route('/stop_server', methods=['POST'])
def stop_server():
    global chat_server
    if chat_server:
        chat_server.stop_server()
        chat_server = None
        return jsonify({'success': True, 'message': '服务器已停止'})
    return jsonify({'success': False, 'message': '服务器未运行'})

@app.route('/connect_client', methods=['POST'])
def connect_client():
    global chat_client
    data = request.json
    host = data.get('host', 'localhost')
    port = int(data.get('port', 8080))
    username = data.get('username', '用户')
    
    if chat_client and chat_client.connected:
        return jsonify({'success': False, 'message': '客户端已连接'})
    
    chat_client = ChatClient(host=host, port=port, username=username)
    if chat_client.connect():
        return jsonify({'success': True, 'message': f'连接服务器成功: {host}:{port}'})
    else:
        return jsonify({'success': False, 'message': '连接服务器失败'})

@app.route('/send_message', methods=['POST'])
def send_message():
    global chat_client
    data = request.json
    content = data.get('content', '')
    
    if chat_client and chat_client.connected:
        if chat_client.send_message(content):
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'message': '发送消息失败'})
    return jsonify({'success': False, 'message': '客户端未连接'})

@app.route('/get_messages', methods=['POST'])
def get_messages():
    """获取新消息的API接口"""
    global chat_client
    data = request.json
    last_id = data.get('last_id', 0)
    
    if chat_client and chat_client.connected:
        messages = chat_client.get_new_messages(last_id)
        return jsonify({
            'success': True,
            'messages': messages,
            'last_id': chat_client.last_message_id if messages else last_id
        })
    else:
        return jsonify({
            'success': False,
            'messages': [],
            'last_id': last_id
        })

@app.route('/disconnect_client', methods=['POST'])
def disconnect_client():
    global chat_client
    if chat_client:
        chat_client.disconnect()
        chat_client = None
        return jsonify({'success': True, 'message': '客户端已断开连接'})
    return jsonify({'success': False, 'message': '客户端未连接'})

# 创建HTML模板目录和文件
def create_template():
    template_dir = os.path.join(os.path.dirname(__file__), 'templates')
    if not os.path.exists(template_dir):
        os.makedirs(template_dir)
    
    html_content = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>局域网聊天工具</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .content {
            display: flex;
            min-height: 600px;
        }
        
        .control-panel {
            width: 300px;
            background: #f8f9fa;
            padding: 25px;
            border-right: 1px solid #e9ecef;
        }
        
        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
        }
        
        .section {
            margin-bottom: 25px;
        }
        
        .section-title {
            font-size: 1.2em;
            font-weight: 600;
            margin-bottom: 15px;
            color: #495057;
            border-bottom: 2px solid #4facfe;
            padding-bottom: 5px;
        }
        
        .input-group {
            margin-bottom: 15px;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: #6c757d;
        }
        
        .input-group input, .input-group select {
            width: 100%;
            padding: 10px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        .input-group input:focus, .input-group select:focus {
            outline: none;
            border-color: #4facfe;
        }
        
        .btn {
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            width: 100%;
            margin-bottom: 10px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
            color: white;
        }
        
        .btn-success {
            background: linear-gradient(135deg, #51cf66 0%, #40c057 100%);
            color: white;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .status {
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            font-size: 14px;
            text-align: center;
        }
        
        .status-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .status-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .status-info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        .messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            max-height: 500px;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 12px;
            border-radius: 10px;
            background: white;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            border-left: 4px solid #4facfe;
        }
        
        .message.system {
            border-left-color: #ffc107;
            background: #fff3cd;
        }
        
        .message.error {
            border-left-color: #dc3545;
            background: #f8d7da;
        }
        
        .message-header {
            font-size: 12px;
            color: #6c757d;
            margin-bottom: 5px;
            font-weight: 600;
        }
        
        .message-content {
            font-size: 14px;
            color: #495057;
            line-height: 1.4;
        }
        
        .input-area {
            padding: 20px;
            background: white;
        }
        
        .message-input {
            display: flex;
            gap: 10px;
        }
        
        .message-input input {
            flex: 1;
            padding: 12px;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            font-size: 14px;
        }
        
        .message-input input:focus {
            outline: none;
            border-color: #4facfe;
        }
        
        .message-input button {
            padding: 12px 25px;
            background: #4facfe;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
        }
        
        .message-input button:hover {
            background: #3a9bf7;
        }
        
        .message-input button:disabled {
            background: #6c757d;
            cursor: not-allowed;
        }
        
        .connection-info {
            background: #e7f3ff;
            padding: 10px;
            border-radius: 5px;
            margin-bottom: 15px;
            font-size: 12px;
            color: #0066cc;
        }
        
        .typing-indicator {
            color: #6c757d;
            font-style: italic;
            font-size: 12px;
            padding: 5px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 安全局域网聊天工具</h1>
            <p>基于Socket的实时通信 - 安全可靠</p>
        </div>
        
        <div class="content">
            <div class="control-panel">
                <div class="section">
                    <div class="section-title">服务器控制</div>
                    <div class="input-group">
                        <label for="serverPort">服务器端口:</label>
                        <input type="number" id="serverPort" value="8080" min="1024" max="65535">
                    </div>
                    <button class="btn btn-primary" onclick="startServer()">启动服务器</button>
                    <button class="btn btn-danger" onclick="stopServer()" disabled>停止服务器</button>
                </div>
                
                <div class="section">
                    <div class="section-title">客户端连接</div>
                    <div class="input-group">
                        <label for="clientHost">服务器地址:</label>
                        <input type="text" id="clientHost" value="localhost" placeholder="例如: 192.168.1.100">
                    </div>
                    <div class="input-group">
                        <label for="clientPort">服务器端口:</label>
                        <input type="number" id="clientPort" value="8080" min="1024" max="65535">
                    </div>
                    <div class="input-group">
                        <label for="username">用户名:</label>
                        <input type="text" id="username" value="用户" placeholder="请输入用户名">
                    </div>
                    <button class="btn btn-success" onclick="connectClient()">连接服务器</button>
                    <button class="btn btn-danger" onclick="disconnectClient()" disabled>断开连接</button>
                </div>
                
                <div id="status" class="status status-info">
                    请启动服务器或连接现有服务器
                </div>
            </div>
            
            <div class="chat-area">
                <div class="messages" id="messages">
                    <div class="connection-info">
                        💡 提示: 先启动服务器，然后连接服务器开始聊天
                    </div>
                </div>
                
                <div class="input-area">
                    <div class="message-input">
                        <input type="text" id="messageInput" placeholder="输入消息..." disabled onkeypress="handleKeyPress(event)">
                        <button onclick="sendMessage()" disabled>发送</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let serverRunning = false;
        let clientConnected = false;
        let lastMessageId = 0;
        let messagePollInterval = null;
        
        function updateUI() {
            document.getElementById('serverPort').disabled = serverRunning;
            document.querySelector('.btn-primary').disabled = serverRunning;
            document.querySelector('.btn-danger').disabled = !serverRunning;
            
            document.getElementById('clientHost').disabled = clientConnected;
            document.getElementById('clientPort').disabled = clientConnected;
            document.getElementById('username').disabled = clientConnected;
            document.querySelector('.btn-success').disabled = clientConnected;
            document.querySelector('.btn-danger').disabled = !clientConnected;
            
            document.getElementById('messageInput').disabled = !clientConnected;
            document.querySelector('.message-input button').disabled = !clientConnected;
        }
        
        function showStatus(message, type = 'info') {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = `status status-${type}`;
        }
        
        function addMessage(data) {
            const messages = document.getElementById('messages');
            
            // 移除连接提示信息
            const connectionInfo = messages.querySelector('.connection-info');
            if (connectionInfo) {
                connectionInfo.remove();
            }
            
            const messageDiv = document.createElement('div');
            
            let messageClass = 'message';
            if (data.type === 'system') messageClass += ' system';
            if (data.type === 'error') messageClass += ' error';
            
            messageDiv.className = messageClass;
            messageDiv.innerHTML = `
                <div class="message-header">
                    ${data.ip || '系统'} | ${data.timestamp || new Date().toLocaleString()}
                </div>
                <div class="message-content">${data.content}</div>
            `;
            
            messages.appendChild(messageDiv);
            messages.scrollTop = messages.scrollHeight;
        }
        
        async function pollMessages() {
            if (!clientConnected) {
                clearInterval(messagePollInterval);
                return;
            }
            
            try {
                const response = await fetch('/get_messages', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ last_id: lastMessageId })
                });
                
                const result = await response.json();
                
                if (result.success && result.messages.length > 0) {
                    result.messages.forEach(message => {
                        addMessage(message);
                        lastMessageId = Math.max(lastMessageId, message.id);
                    });
                }
            } catch (error) {
                console.error('获取消息失败:', error);
            }
        }
        
        function startMessagePolling() {
            if (messagePollInterval) {
                clearInterval(messagePollInterval);
            }
            messagePollInterval = setInterval(pollMessages, 500); // 每500毫秒轮询一次
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        async function startServer() {
            const port = document.getElementById('serverPort').value;
            
            try {
                const response = await fetch('/start_server', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ port: parseInt(port) })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    serverRunning = true;
                    showStatus(result.message, 'success');
                    addMessage({
                        type: 'system',
                        content: '服务器启动成功',
                        timestamp: new Date().toLocaleString()
                    });
                } else {
                    showStatus(result.message, 'error');
                }
                
                updateUI();
            } catch (error) {
                showStatus('服务器启动失败: ' + error.message, 'error');
            }
        }
        
        async function stopServer() {
            try {
                const response = await fetch('/stop_server', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                const result = await response.json();
                
                if (result.success) {
                    serverRunning = false;
                    clientConnected = false;
                    showStatus(result.message, 'success');
                    addMessage({
                        type: 'system',
                        content: '服务器已停止',
                        timestamp: new Date().toLocaleString()
                    });
                    clearInterval(messagePollInterval);
                } else {
                    showStatus(result.message, 'error');
                }
                
                updateUI();
            } catch (error) {
                showStatus('服务器停止失败: ' + error.message, 'error');
            }
        }
        
        async function connectClient() {
            const host = document.getElementById('clientHost').value;
            const port = document.getElementById('clientPort').value;
            const username = document.getElementById('username').value;
            
            if (!username.trim()) {
                showStatus('请输入用户名', 'error');
                return;
            }
            
            try {
                const response = await fetch('/connect_client', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        host: host,
                        port: parseInt(port),
                        username: username
                    })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    clientConnected = true;
                    showStatus(result.message, 'success');
                    addMessage({
                        type: 'system',
                        content: `已连接到服务器 ${host}:${port}`,
                        timestamp: new Date().toLocaleString()
                    });
                    
                    // 开始轮询消息
                    startMessagePolling();
                } else {
                    showStatus(result.message, 'error');
                }
                
                updateUI();
            } catch (error) {
                showStatus('连接服务器失败: ' + error.message, 'error');
            }
        }
        
        async function disconnectClient() {
            try {
                const response = await fetch('/disconnect_client', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    }
                });
                
                const result = await response.json();
                
                if (result.success) {
                    clientConnected = false;
                    showStatus(result.message, 'success');
                    addMessage({
                        type: 'system',
                        content: '已断开服务器连接',
                        timestamp: new Date().toLocaleString()
                    });
                    clearInterval(messagePollInterval);
                } else {
                    showStatus(result.message, 'error');
                }
                
                updateUI();
            } catch (error) {
                showStatus('断开连接失败: ' + error.message, 'error');
            }
        }
        
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const content = input.value.trim();
            
            if (!content) return;
            
            try {
                const response = await fetch('/send_message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ content: content })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    input.value = '';
                } else {
                    showStatus(result.message, 'error');
                }
            } catch (error) {
                showStatus('发送消息失败: ' + error.message, 'error');
            }
        }
        
        updateUI();
    </script>
</body>
</html>
    '''
    
    template_path = os.path.join(template_dir, 'index.html')
    with open(template_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

def main():
    # 创建模板文件
    create_template()
    
    # 启动Flask应用
    print("正在启动局域网聊天工具...")
    print("应用将在Webview窗口中打开")
    print("请确保已安装所需依赖: flask, pywebview")
    
    # 在Webview中打开应用
    webview.create_window(
        "安全局域网聊天工具",
        "http://localhost:5000",
        width=1400,
        height=800,
        resizable=True,
        text_select=True
    )
    
    # 启动Flask服务器（在后台线程）
    def run_flask():
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # 启动Webview
    webview.start()

if __name__ == "__main__":
    main()