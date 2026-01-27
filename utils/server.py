"""
服务器通信模块
包含服务器文件管理、下载、上传、删除、HTTP服务器等功能
增加密码认证、在线编辑txt文件功能
"""
import http.server
import socketserver
import json
import urllib.parse
import os
import base64
import requests
from datetime import datetime
from config.settings import SERVER_USERNAME, SERVER_PASSWORD
from utils.cache import get_cache_folder


def get_auth_header():
    """生成Basic Auth请求头"""
    credentials = f"{SERVER_USERNAME}:{SERVER_PASSWORD}"
    encoded = base64.b64encode(credentials.encode('utf-8')).decode('ascii')
    return f"Basic {encoded}"


def check_auth(handler):
    """检查账号密码认证"""
    auth_header = handler.headers.get('Authorization', '')
    if not auth_header.startswith('Basic '):
        return False
    
    try:
        encoded = auth_header[6:]  # 去掉 "Basic "
        decoded = base64.b64decode(encoded).decode('utf-8')
        username, password = decoded.split(':', 1)
        return username == SERVER_USERNAME and password == SERVER_PASSWORD
    except:
        return False


def fetch_server_files(server_url):
    """从服务器获取文件列表"""
    try:
        headers = {'Authorization': get_auth_header()}
        response = requests.get(f"{server_url}/api/files", headers=headers, timeout=3)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return data.get('files', [])
        return []
    except:
        return []


def download_file_to_cache(server_url, filename):
    """从服务器下载文件到本地缓存，返回本地文件路径"""
    try:
        cache_dir = get_cache_folder()
        headers = {'Authorization': get_auth_header()}
        response = requests.get(f"{server_url}/download/{filename}", headers=headers, timeout=10)
        if response.status_code == 200:
            local_path = os.path.join(cache_dir, filename)
            with open(local_path, 'wb') as f:
                f.write(response.content)
            return local_path
        return None
    except Exception as e:
        print(f"下载文件失败: {e}")
        return None


def fetch_file_content(server_url, filename):
    """从服务器获取文件内容（文本）"""
    try:
        headers = {'Authorization': get_auth_header()}
        response = requests.get(f"{server_url}/download/{filename}", headers=headers, timeout=5)
        if response.status_code == 200:
            return response.content.decode('utf-8', errors='ignore')
        return None
    except:
        return None


def check_server_status(server_url):
    """检查服务器状态"""
    try:
        headers = {'Authorization': get_auth_header()}
        response = requests.get(f"{server_url}/api/status", headers=headers, timeout=2)
        if response.status_code == 200:
            data = response.json()
            return data.get('success', False), data
        return False, None
    except:
        return False, None


class InfoServer:
    """轻量级HTTP服务器，用于信息管理，支持上传、删除、在线编辑txt文件"""
    
    def __init__(self, port=8080):
        self.port = port
        self.info_folder = self.get_info_folder()
        self.running = False
        
    def get_info_folder(self):
        """获取信息存储文件夹"""
        info_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "info")
        info_dir = os.path.abspath(info_dir)
        if not os.path.exists(info_dir):
            os.makedirs(info_dir)
        return info_dir
        
    def start(self):
        """启动服务器"""
        try:
            handler = self.create_handler()
            with socketserver.TCPServer(("", self.port), handler) as httpd:
                print(f"服务器运行在 http://localhost:{self.port}")
                print(f"信息文件夹: {os.path.abspath(self.info_folder)}")
                self.running = True
                httpd.serve_forever()
        except Exception as e:
            print(f"服务器启动失败: {e}")
            return False
        return True
    
    def create_handler(self):
        """创建自定义请求处理器"""
        info_folder = self.info_folder
        
        class DynamicHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                """处理GET请求"""
                path = urllib.parse.urlparse(self.path).path
                
                # 检查认证（排除首页）
                if path != '/' and path != '/index.html' and not check_auth(self):
                    self.send_response(401)
                    self.send_header('WWW-Authenticate', 'Basic realm="Restricted"')
                    self.end_headers()
                    self.wfile.write(b'Unauthorized')
                    return
                
                # 状态API
                if path == '/api/status':
                    files_count = len([f for f in os.listdir(info_folder) if os.path.isfile(os.path.join(info_folder, f))])
                    self.send_json_response({
                        'success': True,
                        'port': self.server.server_address[1],
                        'files_count': files_count
                    })
                # 列出文件API
                elif path == '/api/files':
                    self.send_json_response(self.list_files())
                # 下载文件API
                elif path.startswith('/download/'):
                    filename = urllib.parse.unquote(path[10:])
                    filepath = os.path.join(info_folder, filename)
                    if os.path.exists(filepath):
                        self.send_file(filepath)
                    else:
                        self.send_error(404, "文件不存在")
                # 获取文件内容API（用于在线编辑）
                elif path.startswith('/api/content/'):
                    filename = urllib.parse.unquote(path[13:])
                    filepath = os.path.join(info_folder, filename)
                    if os.path.exists(filepath):
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()
                            self.send_json_response({
                                'success': True,
                                'filename': filename,
                                'content': content
                            })
                        except Exception as e:
                            self.send_json_response({'success': False, 'message': str(e)})
                    else:
                        self.send_error(404, "文件不存在")
                # 默认返回前端页面
                else:
                    self.serve_frontend()
                    
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
                # 更新文件内容（在线编辑）
                elif path == '/api/update':
                    self.handle_update()
                # 删除文件
                elif path == '/api/delete':
                    self.handle_delete()
                else:
                    self.send_error(404, "API不存在")
            
            def list_files(self):
                """列出文件"""
                files = []
                if os.path.exists(info_folder):
                    for filename in os.listdir(info_folder):
                        filepath = os.path.join(info_folder, filename)
                        if os.path.isfile(filepath):
                            stat = os.stat(filepath)
                            ext = os.path.splitext(filename)[1].lower()
                            # 判断是否是文本文件（可在线编辑）
                            is_editable = ext in ['.txt', '.md', '.log', '.json', '.xml', '.ini', '.conf', '.py', '.js', '.html', '.css', '.yaml', '.yml']
                            files.append({
                                'name': filename,
                                'size': self.format_size(stat.st_size),
                                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                                'editable': is_editable,
                                'type': 'image' if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif'] else 'text'
                            })
                return {'success': True, 'files': files, 'count': len(files)}
            
            def handle_upload(self):
                """处理文件上传"""
                try:
                    content_length = int(self.headers.get('Content-Length', 0))
                    post_data = self.rfile.read(content_length)
                    
                    import re
                    data_str = post_data.decode('utf-8', errors='ignore')
                    
                    filename_match = re.search(r'filename="(.+?)"', data_str)
                    
                    if filename_match:
                        filename = os.path.basename(filename_match.group(1))
                        ext = os.path.splitext(filename)[1].lower()
                        
                        filepath = os.path.join(info_folder, filename)
                        
                        # 图片文件直接保存二进制
                        if ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                            # 提取二进制数据
                            boundary_match = re.search(rb'Content-Type: image/.*?\r\n\r\n', post_data)
                            if boundary_match:
                                start = boundary_match.end()
                                end_match = re.search(rb'\r\n--', post_data[start:])
                                if end_match:
                                    end = start + end_match.start()
                                    image_data = post_data[start:end]
                                    with open(filepath, 'wb') as f:
                                        f.write(image_data)
                                else:
                                    raise Exception("无法解析图片数据")
                            else:
                                raise Exception("无法解析图片数据")
                        else:
                            # 文本文件
                            content_match = re.search(r'\r\n\r\n(.+?)\r\n--', data_str, re.DOTALL)
                            if content_match:
                                content = content_match.group(1)
                                with open(filepath, 'w', encoding='utf-8') as f:
                                    f.write(content)
                            else:
                                raise Exception("无法解析文件内容")
                        
                        self.send_json_response({'success': True, 'message': f'上传成功: {filename}'})
                    else:
                        self.send_json_response({'success': False, 'message': '解析上传数据失败'})
                except Exception as e:
                    self.send_json_response({'success': False, 'message': f'上传失败: {str(e)}'})
            
            def handle_update(self):
                """更新文件内容（在线编辑）"""
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
                    filepath = os.path.join(info_folder, filename)
                    
                    if not os.path.exists(filepath):
                        self.send_json_response({'success': False, 'message': '文件不存在'})
                        return
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    self.send_json_response({'success': True, 'message': f'更新成功: {filename}'})
                except Exception as e:
                    self.send_json_response({'success': False, 'message': str(e)})
            
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
                    filepath = os.path.join(info_folder, filename)
                    
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        self.send_json_response({'success': True, 'message': f'删除成功: {filename}'})
                    else:
                        self.send_json_response({'success': False, 'message': '文件不存在'})
                except Exception as e:
                    self.send_json_response({'success': False, 'message': f'删除失败: {str(e)}'})
            
            def serve_frontend(self):
                """提供前端HTML页面（包含上传、删除、在线编辑功能）"""
                html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>配置信息管理服务器</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: "Microsoft YaHei", Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        h1 { color: white; text-align: center; margin-bottom: 30px; font-size: 32px; }
        .card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .card h2 { margin-bottom: 15px; color: #333; display: flex; align-items: center; }
        .btn { padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; margin: 5px; transition: all 0.3s; }
        .btn:hover { opacity: 0.8; transform: translateY(-2px); }
        .btn-primary { background: #2563EB; color: white; }
        .btn-success { background: #16A34A; color: white; }
        .btn-warning { background: #F59E0B; color: white; }
        .btn-danger { background: #DC2626; color: white; }
        .file-list { list-style: none; }
        .file-item { padding: 15px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; transition: background 0.2s; }
        .file-item:hover { background: #f9fafb; }
        .file-info { flex: 1; }
        .file-name { font-weight: bold; color: #2563EB; font-size: 16px; }
        .file-meta { font-size: 12px; color: #6B7280; margin-top: 5px; }
        .editable-badge { background: #10B981; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px; margin-left: 10px; }
        .upload-area { border: 2px dashed #ccc; border-radius: 10px; padding: 40px; text-align: center; cursor: pointer; transition: all 0.3s; }
        .upload-area:hover { border-color: #2563EB; background: #f0f9ff; }
        .upload-area p { color: #666; font-size: 16px; margin-bottom: 10px; }
        .upload-hint { color: #999; font-size: 14px; }
        .editor { display: none; margin-top: 20px; }
        .editor textarea { width: 100%; height: 500px; padding: 15px; font-family: "Consolas", "Monaco", "Courier New", monospace; font-size: 14px; border: 2px solid #ddd; border-radius: 8px; line-height: 1.6; background: #f8f9fa; resize: vertical; }
        .editor textarea:focus { outline: none; border-color: #2563EB; background: white; }
        .editor-toolbar { margin: 10px 0; padding: 10px; background: #f0f0f0; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; }
        .editor-info { color: #666; font-size: 13px; }
        .fullscreen { position: fixed; top: 0; left: 0; right: 0; bottom: 0; z-index: 9999; background: white; padding: 20px; overflow-y: auto; }
        .fullscreen textarea { height: calc(100vh - 200px); }
    </style>
</head>
<body>
    <div class="container">
        <h1>📁 配置信息管理服务器</h1>
        
        <div class="card">
            <h2>📂 文件列表</h2>
            <button class="btn btn-primary" onclick="refreshFiles()">🔄 刷新列表</button>
            <ul class="file-list" id="fileList"></ul>
        </div>
        
        <div class="card">
            <h2>📤 上传文件</h2>
            <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                <p>📎 点击选择文件上传</p>
                <span class="upload-hint">支持 txt, md, 图片 等文件</span>
            </div>
            <input type="file" id="fileInput" style="display: none;" onchange="uploadFile(event)">
        </div>
        
        <div class="card editor" id="editor">
            <h2>✏️ 在线编辑器</h2>
            <div class="editor-toolbar">
                <div class="editor-info">
                    文件: <strong id="editingFile"></strong> | 
                    <span id="charCount">0</span> 字符 | 
                    <span id="lineCount">0</span> 行
                </div>
                <div>
                    <button class="btn btn-primary" onclick="toggleFullscreen()" title="全屏编辑">🔲 全屏</button>
                </div>
            </div>
            <textarea id="editorContent" placeholder="在此编辑文件内容..." oninput="updateStats()"></textarea>
            <div style="margin-top: 15px;">
                <button class="btn btn-success" onclick="saveFile()">💾 保存 (Ctrl+S)</button>
                <button class="btn btn-warning" onclick="closeEditor()">❌ 关闭 (Esc)</button>
                <span style="color: #999; margin-left: 15px; font-size: 13px;">提示: Ctrl+S 快速保存, Esc 关闭编辑器</span>
            </div>
        </div>
    </div>
    
    <script>
        let currentFile = '';
        
        async function refreshFiles() {
            try {
                const response = await fetch('/api/files');
                const data = await response.json();
                const fileList = document.getElementById('fileList');
                fileList.innerHTML = '';
                
                if (data.files && data.files.length > 0) {
                    data.files.forEach(file => {
                        const li = document.createElement('li');
                        li.className = 'file-item';
                        
                        const fileInfo = document.createElement('div');
                        fileInfo.className = 'file-info';
                        
                        const fileName = document.createElement('div');
                        fileName.className = 'file-name';
                        fileName.textContent = file.name;
                        
                        if (file.editable) {
                            const badge = document.createElement('span');
                            badge.className = 'editable-badge';
                            badge.textContent = '可编辑';
                            fileName.appendChild(badge);
                        }
                        
                        const fileMeta = document.createElement('div');
                        fileMeta.className = 'file-meta';
                        fileMeta.textContent = '大小: ' + file.size + ' | 修改时间: ' + file.modified;
                        
                        fileInfo.appendChild(fileName);
                        fileInfo.appendChild(fileMeta);
                        
                        const btnGroup = document.createElement('div');
                        
                        if (file.editable) {
                            const editBtn = document.createElement('button');
                            editBtn.className = 'btn btn-warning';
                            editBtn.textContent = '✏️ 编辑';
                            editBtn.onclick = function() { editFile(file.name); };
                            btnGroup.appendChild(editBtn);
                        }
                        
                        const downloadBtn = document.createElement('button');
                        downloadBtn.className = 'btn btn-primary';
                        downloadBtn.textContent = '⬇️ 下载';
                        downloadBtn.onclick = function() { downloadFile(file.name); };
                        btnGroup.appendChild(downloadBtn);
                        
                        const deleteBtn = document.createElement('button');
                        deleteBtn.className = 'btn btn-danger';
                        deleteBtn.textContent = '🗑️ 删除';
                        deleteBtn.onclick = function() { deleteFile(file.name); };
                        btnGroup.appendChild(deleteBtn);
                        
                        li.appendChild(fileInfo);
                        li.appendChild(btnGroup);
                        fileList.appendChild(li);
                    });
                } else {
                    fileList.innerHTML = '<li class="file-item">暂无文件</li>';
                }
            } catch (error) {
                console.error('刷新文件列表失败:', error);
                alert('刷新文件列表失败: ' + error.message);
            }
        }
        
        async function uploadFile(event) {
            const file = event.target.files[0];
            if (!file) return;
            
            try {
                const formData = new FormData();
                formData.append('file', file);
                
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('上传成功！');
                    refreshFiles();
                } else {
                    alert('上传失败: ' + data.message);
                }
            } catch (error) {
                alert('上传失败: ' + error.message);
            }
            
            // 清空文件选择
            event.target.value = '';
        }
        
        async function editFile(filename) {
            try {
                const response = await fetch('/api/content/' + encodeURIComponent(filename));
                const data = await response.json();

                if (data.success) {
                    currentFile = filename;
                    document.getElementById('editingFile').textContent = filename;
                    document.getElementById('editorContent').value = data.content;
                    updateStats();
                    document.getElementById('editor').style.display = 'block';
                    document.getElementById('editor').scrollIntoView({ behavior: 'smooth' });
                    
                    // 聚焦到编辑器
                    setTimeout(() => {
                        document.getElementById('editorContent').focus();
                    }, 300);
                } else {
                    alert('加载文件失败: ' + data.message);
                }
            } catch (error) {
                alert('加载文件失败: ' + error.message);
            }
        }
        
        function updateStats() {
            const content = document.getElementById('editorContent').value;
            const charCount = content.length;
            const lineCount = content.split('\\n').length;
            
            document.getElementById('charCount').textContent = charCount;
            document.getElementById('lineCount').textContent = lineCount;
        }
        
        function toggleFullscreen() {
            const editor = document.getElementById('editor');
            if (editor.classList.contains('fullscreen')) {
                editor.classList.remove('fullscreen');
            } else {
                editor.classList.add('fullscreen');
            }
        }
        
        async function saveFile() {
            try {
                const content = document.getElementById('editorContent').value;
                const response = await fetch('/api/update', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: currentFile, content: content })
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('✅ 保存成功！');
                    refreshFiles();
                } else {
                    alert('❌ 保存失败: ' + data.message);
                }
            } catch (error) {
                alert('保存失败: ' + error.message);
            }
        }
        
        function closeEditor() {
            if (document.getElementById('editorContent').value !== '') {
                if (!confirm('确定要关闭编辑器吗？未保存的修改将丢失！')) {
                    return;
                }
            }
            document.getElementById('editor').style.display = 'none';
            document.getElementById('editor').classList.remove('fullscreen');
            currentFile = '';
        }
        
        // 快捷键支持
        document.addEventListener('keydown', function(e) {
            // Ctrl+S 或 Cmd+S 保存
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                if (currentFile && document.getElementById('editor').style.display !== 'none') {
                    saveFile();
                }
            }
            
            // Esc 关闭编辑器
            if (e.key === 'Escape') {
                if (document.getElementById('editor').style.display !== 'none') {
                    closeEditor();
                }
            }
        });
        
        function downloadFile(filename) {
            window.location.href = '/download/' + encodeURIComponent(filename);
        }
        
        async function deleteFile(filename) {
            if (!confirm('确定要删除 "' + filename + '" 吗？此操作不可恢复！')) {
                return;
            }
            
            try {
                const response = await fetch('/api/delete', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ filename: filename })
                });
                
                const data = await response.json();
                if (data.success) {
                    alert('删除成功！');
                    refreshFiles();
                } else {
                    alert('删除失败: ' + data.message);
                }
            } catch (error) {
                alert('删除失败: ' + error.message);
            }
        }
        
        // 页面加载时刷新文件列表
        refreshFiles();
    </script>
</body>
</html>"""
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(html.encode('utf-8'))
            
            def send_json_response(self, data):
                """发送JSON响应"""
                response = json.dumps(data, ensure_ascii=False)
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(response.encode('utf-8'))
            
            def send_file(self, filepath):
                """发送文件"""
                try:
                    with open(filepath, 'rb') as f:
                        content = f.read()
                    
                    filename = os.path.basename(filepath)
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/octet-stream')
                    self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                    self.send_header('Content-Length', len(content))
                    self.end_headers()
                    self.wfile.write(content)
                except Exception as e:
                    self.send_error(500, str(e))
            
            def format_size(self, size):
                """格式化文件大小"""
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size < 1024:
                        return f"{size:.1f} {unit}"
                    size /= 1024
                return f"{size:.1f} TB"
                    
            def log_message(self, format, *args):
                # 抑制默认的日志输出
                pass
        
        return DynamicHandler


# ===================== 服务器启动入口 =====================
if __name__ == "__main__":
    import sys
    # 添加项目根目录到路径
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, project_root)
    
    port = int(os.environ.get("PORT", 8080))
    server = InfoServer(port=port)
    print(f"正在启动信息服务器，端口: {port}")
    print(f"项目根目录: {project_root}")
    server.start()
