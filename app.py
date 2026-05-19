from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key_gomoku'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

rooms = {}

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('join')
def on_join(data):
    room = data.get('room', 'lobby')
    join_room(room)
    
    if room not in rooms:
        rooms[room] = {'players': [], 'ips': [], 'board': [[0]*15 for _ in range(15)], 'turn': 1}
    
    if request.sid not in rooms[room]['players']:
        if len(rooms[room]['players']) < 2:
            rooms[room]['players'].append(request.sid)
            ip = request.headers.get('X-Forwarded-For', request.remote_addr)
            if ip: ip = ip.split(',')[0].strip()
            rooms[room]['ips'].append(ip)
            
            player_color = 1 if len(rooms[room]['players']) == 1 else 2
            emit('joined', {'color': player_color, 'board': rooms[room]['board'], 'turn': rooms[room]['turn'], 'ips': rooms[room]['ips']}, to=request.sid)
            
            if len(rooms[room]['players']) == 2:
                emit('game_start', {'message': '遊戲開始！', 'ips': rooms[room]['ips']}, to=room)
        else:
            emit('joined', {'color': 0, 'board': rooms[room]['board'], 'turn': rooms[room]['turn'], 'ips': rooms[room]['ips']}, to=request.sid)

@socketio.on('move')
def on_move(data):
    room = data.get('room', 'lobby')
    row = data['row']
    col = data['col']
    color = data['color']
    
    if room in rooms and len(rooms[room]['players']) == 2:
        if rooms[room]['turn'] == color and rooms[room]['board'][row][col] == 0:
            rooms[room]['board'][row][col] = color
            rooms[room]['turn'] = 3 - color
            emit('update_board', {'row': row, 'col': col, 'color': color, 'turn': rooms[room]['turn']}, to=room)

@socketio.on('reset')
def on_reset(data):
    room = data.get('room', 'lobby')
    if room in rooms:
        rooms[room]['board'] = [[0]*15 for _ in range(15)]
        rooms[room]['turn'] = 1
        emit('board_reset', {}, to=room)

@socketio.on('disconnect')
def on_disconnect():
    for room_name, room in rooms.items():
        if request.sid in room['players']:
            idx = room['players'].index(request.sid)
            room['players'].pop(idx)
            if 'ips' in room and len(room['ips']) > idx:
                room['ips'].pop(idx)
            if len(room['players']) < 2:
                emit('board_reset', {}, to=room_name)

if __name__ == '__main__':
    import threading
    import sys
    import webbrowser
    
    def run_server():
        socketio.run(app, debug=False, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
    
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        from PyQt5.QtCore import QUrl, Qt
        
        class GomokuDesktop(QMainWindow):
            def __init__(self, url):
                super().__init__()
                self.url = url
                self.setWindowTitle("線上五子棋 - 桌面端")
                self.resize(550, 800)
                
                qr = self.frameGeometry()
                cp = QApplication.desktop().availableGeometry().center()
                qr.moveCenter(cp)
                self.move(qr.topLeft())

                main_widget = QWidget()
                self.setCentralWidget(main_widget)
                main_widget.setStyleSheet("background-color: #f2f2f7;")
                
                layout = QVBoxLayout(main_widget)
                layout.setContentsMargins(0, 0, 0, 0)
                layout.setSpacing(0)

                top_bar = QWidget()
                top_bar.setFixedHeight(60)
                top_bar.setStyleSheet("""
                    QWidget {
                        background-color: rgba(255, 255, 255, 0.9);
                        border-bottom: 1px solid rgba(60, 60, 67, 0.18);
                    }
                """)
                top_layout = QHBoxLayout(top_bar)
                top_layout.setContentsMargins(15, 0, 15, 0)

                title = QLabel("五子棋連線大廳")
                title.setStyleSheet("""
                    font-size: 18px; 
                    font-weight: bold; 
                    color: #1c1c1e;
                    border: none;
                    background: transparent;
                """)
                
                web_btn = QPushButton("開啟網頁版")
                web_btn.setCursor(Qt.PointingHandCursor)
                web_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #007aff;
                        color: white;
                        border-radius: 15px;
                        padding: 8px 15px;
                        font-size: 14px;
                        font-weight: bold;
                        border: none;
                    }
                    QPushButton:hover {
                        background-color: #005bb5;
                    }
                    QPushButton:pressed {
                        background-color: #003d82;
                    }
                """)
                web_btn.clicked.connect(self.open_browser)

                top_layout.addWidget(title)
                top_layout.addStretch()
                top_layout.addWidget(web_btn)

                self.browser = QWebEngineView()
                self.browser.load(QUrl(url))
                
                layout.addWidget(top_bar)
                layout.addWidget(self.browser)

            def open_browser(self):
                webbrowser.open(self.url)
                
        qt_app = QApplication(sys.argv)
        target_url = "http://127.0.0.1:5000"
        window = GomokuDesktop(target_url)
        window.show()
        sys.exit(qt_app.exec_())
    except ImportError:
        print("Running in server-only mode (No PyQt5 found).")
        server_thread.join()
