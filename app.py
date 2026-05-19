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
                emit('board_reset', {}, to=room_name) # Tell remaining player it's reset

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
