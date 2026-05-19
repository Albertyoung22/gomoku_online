const socket = io();
const canvas = document.getElementById('gomokuBoard');
const ctx = canvas.getContext('2d');
const statusEl = document.getElementById('status');
const resetBtn = document.getElementById('resetBtn');

const GRID_SIZE = 30;
const BOARD_SIZE = 15;
const MARGIN = 15;

let myColor = 0; // 1: black, 2: white, 0: spectator
let currentTurn = 1;
let board = Array(BOARD_SIZE).fill().map(() => Array(BOARD_SIZE).fill(0));
let gameActive = false;

// Initialize connection
socket.on('connect', () => {
    socket.emit('join', {room: 'lobby'});
});

socket.on('joined', (data) => {
    myColor = data.color;
    board = data.board;
    currentTurn = data.turn;
    updateIPs(data.ips);
    drawBoard();
    updateStatus();
});

function updateIPs(ips) {
    if (!ips) return;
    document.getElementById('black-ip').innerText = ips.length > 0 ? "IP: " + ips[0] : "IP: 等待中...";
    document.getElementById('white-ip').innerText = ips.length > 1 ? "IP: " + ips[1] : "IP: 等待中...";
}

socket.on('game_start', (data) => {
    gameActive = true;
    updateIPs(data.ips);
    updateStatus();
});

socket.on('update_board', (data) => {
    board[data.row][data.col] = data.color;
    currentTurn = data.turn;
    drawBoard();
    checkWinLocal(data.row, data.col, data.color);
    updateStatus();
});

socket.on('board_reset', () => {
    board = Array(BOARD_SIZE).fill().map(() => Array(BOARD_SIZE).fill(0));
    currentTurn = 1;
    gameActive = true;
    // reset ips if needed, actually keep them or clear based on who left. 
    // Usually handled by the server emitting new IPs on reset if we wanted.
    drawBoard();
    updateStatus();
});

function updateStatus() {
    if (myColor === 0) {
        statusEl.innerText = "觀戰模式";
    } else if (!gameActive && board.every(row => row.every(cell => cell === 0))) {
        statusEl.innerText = "等待對手加入...";
    } else {
        if (myColor === currentTurn) {
            statusEl.innerText = "輪到您了！";
            statusEl.style.color = "#007aff";
        } else {
            statusEl.innerText = "對手思考中...";
            statusEl.style.color = "#8e8e93";
        }
    }
}

function drawBoard() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    ctx.beginPath();
    ctx.strokeStyle = "#000";
    ctx.lineWidth = 1;
    
    for (let i = 0; i < BOARD_SIZE; i++) {
        ctx.moveTo(MARGIN, MARGIN + i * GRID_SIZE);
        ctx.lineTo(MARGIN + (BOARD_SIZE - 1) * GRID_SIZE, MARGIN + i * GRID_SIZE);
        ctx.moveTo(MARGIN + i * GRID_SIZE, MARGIN);
        ctx.lineTo(MARGIN + i * GRID_SIZE, MARGIN + (BOARD_SIZE - 1) * GRID_SIZE);
    }
    ctx.stroke();

    for (let r = 0; r < BOARD_SIZE; r++) {
        for (let c = 0; c < BOARD_SIZE; c++) {
            if (board[r][c] !== 0) {
                drawPiece(r, c, board[r][c]);
            }
        }
    }
}

function drawPiece(row, col, color) {
    const x = MARGIN + col * GRID_SIZE;
    const y = MARGIN + row * GRID_SIZE;
    
    ctx.beginPath();
    ctx.arc(x, y, 13, 0, 2 * Math.PI);
    
    const gradient = ctx.createRadialGradient(x - 4, y - 4, 2, x, y, 13);
    if (color === 1) { 
        gradient.addColorStop(0, '#666');
        gradient.addColorStop(1, '#000');
    } else { 
        gradient.addColorStop(0, '#fff');
        gradient.addColorStop(1, '#ccc');
    }
    
    ctx.fillStyle = gradient;
    ctx.fill();
    ctx.shadowColor = 'rgba(0, 0, 0, 0.3)';
    ctx.shadowBlur = 4;
    ctx.shadowOffsetX = 2;
    ctx.shadowOffsetY = 2;
}

canvas.addEventListener('click', (e) => {
    if (!gameActive || myColor === 0 || myColor !== currentTurn) return;

    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    const col = Math.round((x - MARGIN) / GRID_SIZE);
    const row = Math.round((y - MARGIN) / GRID_SIZE);

    if (row >= 0 && row < BOARD_SIZE && col >= 0 && col < BOARD_SIZE) {
        if (board[row][col] === 0) {
            socket.emit('move', {room: 'lobby', row: row, col: col, color: myColor});
        }
    }
});

resetBtn.addEventListener('click', () => {
    if (myColor !== 0) {
        socket.emit('reset', {room: 'lobby'});
    }
});

function checkWinLocal(row, col, color) {
    const directions = [
        [1, 0], [0, 1], [1, 1], [1, -1]
    ];
    
    for (let [dr, dc] of directions) {
        let count = 1;
        for (let i = 1; i <= 4; i++) {
            const r = row + dr * i;
            const c = col + dc * i;
            if (r >= 0 && r < BOARD_SIZE && c >= 0 && c < BOARD_SIZE && board[r][c] === color) count++;
            else break;
        }
        for (let i = 1; i <= 4; i++) {
            const r = row - dr * i;
            const c = col - dc * i;
            if (r >= 0 && r < BOARD_SIZE && c >= 0 && c < BOARD_SIZE && board[r][c] === color) count++;
            else break;
        }
        if (count >= 5) {
            gameActive = false;
            setTimeout(() => {
                alert((color === 1 ? '黑子' : '白子') + ' 獲勝！');
            }, 100);
            return;
        }
    }
}
