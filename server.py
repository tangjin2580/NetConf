#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置信息服务器
提供REST API接口，供客户端拉取配置信息
"""

import http.server
import socketserver
import json
import os
import urllib.parse
from datetime import datetime

# 配置
PORT = 8080
# 账号密码认证
USERNAME = "info"
PASSWORD = "mecPassw0rd"
# 使用脚本所在目录的绝对路径，确保Windows部署正常
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
INFO_FOLDER = os.path.join(SCRIPT_DIR, "info")

# 确保info文件夹存在
if not os.path.exists(INFO_FOLDER):
    os.makedirs(INFO_FOLDER)

def check_auth(handler):
    """检查账号密码认证"""
    auth_header = handler.headers.get('Authorization', '')
    if not auth_header.startswith('Basic '):
        return False
    
    import base64
    try:
        encoded = auth_header[6:]  # 去掉 "Basic "
        decoded = base64.b64decode(encoded).decode('utf-8')
        username, password = decoded.split(':', 1)
        return username == USERNAME and password == PASSWORD
    except:
        return False

class ConfigAPIHandler(http.server.SimpleHTTPRequestHandler):
    """API请求处理器"""
    
    def end_headers(self):
        """重写end_headers以添加CORS头"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_GET(self):
        """处理GET请求"""
        path = urllib.parse.urlparse(self.path).path
        
        # 检查认证（排除首页和管理页面）
        if path != '/' and path != '/index.html' and not check_auth(self):
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Restricted"')
            self.end_headers()
            self.wfile.write(b'Unauthorized')
            return
        
        # 列出文件API
        if path == '/api/files':
            self.send_json_response(self.list_files())
        # 获取服务器状态
        elif path == '/api/status':
            self.send_json_response(self.get_status())
        # 下载文件
        elif path.startswith('/download/'):
            filename = urllib.parse.unquote(path[10:])
            filepath = os.path.join(INFO_FOLDER, filename)
            if os.path.exists(filepath):
                self.send_file(filepath)
            else:
                self.send_error_utf8(404, "文件不存在")
        # 默认返回前端页面
        elif path == '/' or path == '/index.html':
            self.send_html(self.get_index_page())
        else:
            self.send_error_utf8(404, "API不存在")
    
    def do_POST(self):
        """处理POST请求"""
        # 检查认证
        if not check_auth(self):
            self.send_response(401)
            self.send_header('WWW-Authenticate', 'Basic realm="Restricted"')
            self.end_headers()
            self.wfile.write(b'Unauthorized')
            return
        
        path = urllib.parse.urlparse(self.path).path
        
        # 上传文件
        if path == '/api/upload':
            self.handle_upload()
        # 保存文件
        elif path == '/api/save':
            self.handle_save()
        # 删除文件
        elif path == '/api/delete':
            self.handle_delete()
        else:
            self.send_error(404, "API not found")
    
    def list_files(self):
        """列出文件"""
        files = []
        if os.path.exists(INFO_FOLDER):
            for filename in os.listdir(INFO_FOLDER):
                filepath = os.path.join(INFO_FOLDER, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    ext = os.path.splitext(filename)[1].lower()
                    files.append({
                        'name': filename,
                        'size': self.format_size(stat.st_size),
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'type': 'image' if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif'] else 'text'
                    })
        return {
            'success': True, 
            'files': files,
            'count': len(files)
        }
    
    def get_status(self):
        """获取服务器状态"""
        return {
            'success': True,
            'status': 'running',
            'port': PORT,
            'folder': INFO_FOLDER,
            'files_count': len([f for f in os.listdir(INFO_FOLDER) if os.path.isfile(os.path.join(INFO_FOLDER, f))]) if os.path.exists(INFO_FOLDER) else 0
        }
    
    def handle_upload(self):
        """处理文件上传"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            import re
            data_str = post_data.decode('utf-8', errors='ignore')
            
            filename_match = re.search(r'filename="(.+?)"', data_str)
            content_match = re.search(r'\r\n\r\n(.+?)\r\n--', data_str, re.DOTALL)
            
            if filename_match and content_match:
                filename = os.path.basename(filename_match.group(1))
                ext = os.path.splitext(filename)[1].lower()
                
                if ext not in ['.txt', '.md', '.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                    self.send_json_response({'success': False, 'message': '不支持的文件类型'})
                    return
                
                content = content_match.group(1)
                filepath = os.path.join(INFO_FOLDER, filename)
                
                if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                    with open(filepath, 'wb') as f:
                        f.write(post_data)
                else:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                
                self.send_json_response({
                    'success': True, 
                    'message': f'上传成功: {filename}',
                    'filename': filename
                })
            else:
                self.send_json_response({'success': False, 'message': '解析上传数据失败'})
        except Exception as e:
            self.send_json_response({'success': False, 'message': f'上传失败: {str(e)}'})
    
    def handle_save(self):
        """保存文件"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            filename = data.get('filename', '')
            content = data.get('content', '')
            
            if not filename:
                self.send_json_response({'success': False, 'message': '文件名不能为空'})
                return
            
            filename = os.path.basename(filename)
            ext = os.path.splitext(filename)[1].lower()
            
            if ext not in ['.txt', '.md']:
                self.send_json_response({'success': False, 'message': '只能编辑文本文件'})
                return
            
            filepath = os.path.join(INFO_FOLDER, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.send_json_response({
                'success': True, 
                'message': f'保存成功: {filename}',
                'filename': filename
            })
        except Exception as e:
            self.send_json_response({'success': False, 'message': f'保存失败: {str(e)}'})
    
    def handle_delete(self):
        """删除文件"""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            filename = data.get('filename', '')
            if not filename:
                self.send_json_response({'success': False, 'message': '文件名不能为空'})
                return
            
            filename = os.path.basename(filename)
            filepath = os.path.join(INFO_FOLDER, filename)
            
            if os.path.exists(filepath):
                os.remove(filepath)
                self.send_json_response({
                    'success': True, 
                    'message': f'删除成功: {filename}'
                })
            else:
                self.send_json_response({'success': False, 'message': '文件不存在'})
        except Exception as e:
            self.send_json_response({'success': False, 'message': f'删除失败: {str(e)}'})
    
    def send_json_response(self, data):
        """发送JSON响应"""
        response = json.dumps(data, ensure_ascii=False)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def send_error_utf8(self, code, message):
        """发送UTF-8编码的错误响应"""
        response = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>Error {code}</title>
</head>
<body>
    <h1>Error {code}</h1>
    <p>{message}</p>
</body>
</html>"""
        self.send_response(code)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', len(response.encode('utf-8')))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))
    
    def send_file(self, filepath):
        """发送文件"""
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            
            filename = os.path.basename(filepath)
            ext = os.path.splitext(filename)[1].lower()
            
            mime_types = {
                '.txt': 'text/plain',
                '.md': 'text/markdown',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.bmp': 'image/bmp',
                '.gif': 'image/gif'
            }
            
            self.send_response(200)
            self.send_header('Content-Type', mime_types.get(ext, 'application/octet-stream'))
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Content-Length', len(content))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error_utf8(500, f'发送文件失败: {str(e)}')
    
    def send_html(self, html):
        """发送HTML页面"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def get_index_page(self):
        """获取管理页面HTML"""
        return '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>配置信息管理服务器</title>
    <style>
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: white; text-align: center; margin-bottom: 30px; }
        .card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; }
        .btn { padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .btn-primary { background: #2563EB; color: white; }
        .btn-success{ background: #16A34A; color: white; }
        .btn-danger { background: #DC2626; color: white; }
        .file-item { display: flex; justify-content: space-between; padding: 15px; border-bottom: 1px solid #eee; }
        .upload-area { border: 2px dashed #ccc; border-radius: 10px; padding: 40px; text-align: center; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <h1>配置信息管理服务器</h1>
        <div class="card">
            <h2>文件列表</h2>
            <ul class="file-list" id="fileList"><li>加载中...</li></ul>
        </div>
        <div class="card">
            <h2>上传文件</h2>
            <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                <p>点击上传文件 (支持 txt, md, 图片)</p>
            </div>
            <input type="file" id="fileInput" style="display: none;" onchange="handleFileSelect(event)">
        </div>
    </div>
    <script>
        async function loadFiles() {
            const list = document.getElementById('fileList');
            try {
                const res = await fetch('/api/files');
                if (!res.ok) {
                    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
                }
                const data = await res.json();
                
                if (data.files && data.files.length > 0) {
                    list.innerHTML = data.files.map(f => `
                        <li class="file-item">
                            <span>${f.name} (${f.size})</span>
                            <div>
                                <button class="btn btn-primary" onclick="downloadFile('${f.name}')">下载</button>
                                <button class="btn btn-danger" onclick="deleteFile('${f.name}')">删除</button>
                            </div>
                        </li>
                    `).join('');
                } else {
                    list.innerHTML = '<li>暂无文件</li>';
                }
            } catch (err) {
                console.error('加载文件列表失败:', err);
                list.innerHTML = `<li style="color: red;">加载失败: ${err.message}</li>`;
            }
        }
        
        async function handleFileSelect(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const res = await fetch('/api/upload', { method: 'POST', body: formData });
                const data = await res.json();
                alert(data.message);
                loadFiles();
            } catch (err) {
                alert('上传失败: ' + err.message);
            }
        }
        
        function downloadFile(filename) {
            window.location.href = '/download/' + filename;
        }
        
        async function deleteFile(filename) {
            if (!confirm('确定删除?')) return;
            try {
                const res = await fetch('/api/delete', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({filename})
                });
                const data = await res.json();
                alert(data.message);
                loadFiles();
            } catch (err) {
                alert('删除失败: ' + err.message);
            }
        }
        
        loadFiles();
    </script>
</body>
</html>'''
    
    def format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    
    def do_OPTIONS(self):
        """处理CORS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()
    
    def log_message(self, format, *args):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {format % args}")

class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True

def run_server():
    try:
        with ThreadedHTTPServer(("", PORT), ConfigAPIHandler) as httpd:
            print(f"\n服务器已启动!")
            print(f"访问地址: http://localhost:{PORT}")
            print(f"信息文件夹: {os.path.abspath(INFO_FOLDER)}\n")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n服务器已停止")

if __name__ == "__main__":
    run_server()
