document.addEventListener('DOMContentLoaded', function() {
    let currentGameId = null;
    let currentGameUuid = null;
    let currentGameData = null;
    let gameSocket = null;

    const gameIdSpan = document.getElementById('game-id');
    const boardDiv = document.getElementById('board');
    const messageDiv = document.getElementById('message');
    const gameTypeSelect = document.getElementById('game-type-select');
    const difficultyPanel = document.getElementById('difficulty-panel');
    const difficultySelect = document.getElementById('difficulty-select');
    const resetBtn = document.getElementById('reset-btn');
    const siteWrapper = document.querySelector('.site-wrapper');
    const combatHud = document.getElementById('combat-hud');
    const playerHpBar = document.getElementById('player-hp-bar');
    const enemyHpBar = document.getElementById('enemy-hp-bar');
    const playerHpText = document.getElementById('player-hp-text');
    const enemyHpText = document.getElementById('enemy-hp-text');

    // Show/hide difficulty based on mode
    gameTypeSelect.addEventListener('change', function() {
        difficultyPanel.style.display = (this.value === 'single_player_ai' || this.value === 'roguelike') ? 'flex' : 'none';
    });

    function connectWebSocket(uuid) {
        if (gameSocket) gameSocket.close();
        const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        gameSocket = new WebSocket(`${protocol}${window.location.host}/ws/play/${uuid}/`);
        
        gameSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            if (data.error) showMessage(data.error, true);
            else updateGameState(data);
        };
        
        gameSocket.onclose = function(e) { console.log('Socket closed'); };
    }

    function initBoard(size = 3) {
        boardDiv.innerHTML = '';
        boardDiv.style.gridTemplateColumns = `repeat(${size}, 1fr)`;
        boardDiv.style.gridTemplateRows = `repeat(${size}, 1fr)`;
        boardDiv.style.width = `${size * 116 - 16}px`; // Adjust width based on cells + gaps
        
        for (let i = 0; i < size * size; i++) {
            const cell = document.createElement('div');
            cell.classList.add('cell');
            cell.dataset.index = i;
            cell.addEventListener('click', handleCellClick);
            boardDiv.appendChild(cell);
        }
    }

    function handleCellClick(e) {
        if (!currentGameData || currentGameData.status !== 'playing') return;
        const index = parseInt(e.target.dataset.index);
        
        if (currentGameData.game_type === 'play_vs_friend' && gameSocket && gameSocket.readyState === WebSocket.OPEN) {
            gameSocket.send(JSON.stringify({ action: 'move', position: index }));
        } else {
            fetch(`/tictactoe/${currentGameId}/move/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify({ position: index })
            })
            .then(res => res.json())
            .then(data => data.error ? showMessage(data.error, true) : updateGameState(data))
            .catch(err => showMessage('Error: ' + err, true));
        }
    }

    function updateGameState(data) {
        if (!currentGameData || data.size !== currentGameData.size) initBoard(data.size);
        currentGameData = data;
        currentGameId = data.id;
        currentGameUuid = data.uuid;
        gameIdSpan.textContent = data.id;

        const cells = boardDiv.querySelectorAll('.cell');
        cells.forEach((cell, i) => {
            const val = data.board[i];
            cell.textContent = val === '_' ? '' : val;
            if (val !== '_') {
                cell.classList.add('taken');
                cell.setAttribute('data-value', val);
            } else {
                cell.classList.remove('taken');
                cell.removeAttribute('data-value');
            }
            // Mark hazards
            if (data.hazards && data.hazards.includes(i)) {
                cell.classList.add('hazard');
                cell.textContent = '!';
            }
        });

        // HP and HUD
        if (data.game_type === 'roguelike') {
            combatHud.classList.remove('hidden');
            updateHP(playerHpBar, playerHpText, data.player_hp);
            updateHP(enemyHpBar, enemyHpText, data.enemy_hp);
        } else {
            combatHud.classList.add('hidden');
        }

        // Status and Animations
        siteWrapper.classList.remove('win-animation');
        let msg = data.status === 'playing' ? `Player ${data.current_player}'s turn` : 
                  data.status === 'draw' ? "It's a draw!" : `Player ${data.status[0]} Wins!`;
        
        if (data.status !== 'playing') {
            siteWrapper.classList.add('win-animation');
            setTimeout(() => newGame(gameTypeSelect.value, difficultySelect.value), 3000);
        }
        showMessage(msg, false);
    }

    function updateHP(bar, text, val) {
        const pct = (val / 20) * 100;
        bar.style.width = `${Math.max(0, pct)}%`;
        text.textContent = `${val}/20`;
    }

    function showMessage(text, isError) {
        messageDiv.textContent = text;
        messageDiv.style.borderStyle = isError ? 'solid' : 'dashed';
        messageDiv.style.color = isError ? '#DC2626' : 'inherit';
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    function newGame(type, diff) {
        fetch('/tictactoe/create/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ game_type: type, difficulty: diff })
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) return showMessage(data.error, true);
            if (type === 'play_vs_friend') connectWebSocket(data.uuid);
            updateGameState(data);
        });
    }

    resetBtn.addEventListener('click', () => newGame(gameTypeSelect.value, difficultySelect.value));
    
    // Initial Load
    const initialId = boardDiv.dataset.initialId;
    if (initialId) {
        fetch(`/tictactoe/${initialId}/`)
        .then(res => res.json())
        .then(data => {
            if (data.game_type === 'play_vs_friend') connectWebSocket(data.uuid);
            updateGameState(data);
        })
        .catch(() => newGame(gameTypeSelect.value, difficultySelect.value));
    } else {
        newGame(gameTypeSelect.value, difficultySelect.value);
    }
});
