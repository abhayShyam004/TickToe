document.addEventListener('DOMContentLoaded', function() {
    let currentGameId = null;
    let currentGameData = null;

    const gameIdSpan = document.getElementById('game-id');
    const boardDiv = document.getElementById('board');
    const messageDiv = document.getElementById('message');
    const gameTypeSelect = document.getElementById('game-type-select');
    const difficultyPanel = document.getElementById('difficulty-panel');
    const difficultySelect = document.getElementById('difficulty-select');
    const resetBtn = document.getElementById('reset-btn');

    // Show/hide difficulty based on mode
    gameTypeSelect.addEventListener('change', function() {
        if (this.value === 'single_player_ai' || this.value === 'roguelike') {
            difficultyPanel.classList.remove('hidden');
        } else {
            difficultyPanel.classList.add('hidden');
        }
    });

    // Initialize board cells
    function initBoard() {
        boardDiv.innerHTML = '';
        for (let i = 0; i < 9; i++) {
            const cell = document.createElement('div');
            cell.classList.add('cell');
            cell.dataset.index = i;
            cell.addEventListener('click', handleCellClick);
            boardDiv.appendChild(cell);
        }
    }

    // Handle cell click
    function handleCellClick(e) {
        if (!currentGameId || !currentGameData) return;

        const cell = e.target;
        const index = parseInt(cell.dataset.index);

        // Prevent clicking if game is over
        if (currentGameData.status !== 'playing') {
            return;
        }

        // Check if cell is already taken
        if (currentGameData.board[index] !== '_') {
            showMessage('Invalid move! Cell already taken.', true);
            return;
        }

        // Make move via AJAX
        fetch(`/tictactoe/${currentGameId}/move/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ position: index })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showMessage(data.error, true);
                return;
            }
            updateGameState(data);
        })
        .catch(error => {
            showMessage('Error making move: ' + error, true);
        });
    }

    // Helper to update HP bars
    function updateHP(side, current, max) {
        const bar = document.getElementById(`${side}-hp-bar`);
        const text = document.getElementById(`${side}-hp-text`);
        if (!bar || !text) return;
        const percentage = Math.max(0, (current / max) * 100);
        bar.style.width = `${percentage}%`;
        text.textContent = `${current}/${max}`;
    }

    // Update game state from server response
    function updateGameState(data) {
        currentGameData = data;
        gameIdSpan.textContent = currentGameData.id;

        // Parse hazards
        let hazards = [];
        try {
            hazards = JSON.parse(currentGameData.hazards || '[]');
        } catch (e) {
            console.error('Failed to parse hazards', e);
        }

        // Show combat HUD if in roguelike mode
        const combatHud = document.getElementById('combat-hud');
        if (currentGameData.game_type === 'roguelike') {
            combatHud.classList.remove('hidden');
            updateHP('player', currentGameData.player_hp, 20); // Default max is 20
            updateHP('enemy', currentGameData.enemy_hp, 20); // Default max is 20
        } else {
            combatHud.classList.add('hidden');
        }

        // Update board cells
        const cells = boardDiv.querySelectorAll('.cell');
        cells.forEach((cell, index) => {
            const cellValue = currentGameData.board[index];
            cell.textContent = cellValue === '_' ? '' : cellValue;
            
            // Clear classes
            cell.classList.remove('taken', 'hazard');
            cell.removeAttribute('data-value');

            if (cellValue !== '_') {
                cell.classList.add('taken');
                cell.setAttribute('data-value', cellValue);
            } else if (hazards.includes(index)) {
                cell.classList.add('hazard');
                cell.classList.add('taken');
                cell.textContent = '!'; // Indicator for hazards
            }
        });

        // Update message based on game status
        let message = '';
        const siteWrapper = document.querySelector('.site-wrapper');
        
        // Remove previous animation
        siteWrapper.classList.remove('win-animation');

        switch (currentGameData.status) {
            case 'playing':
                message = `Player ${currentGameData.current_player}'s turn`;
                break;
            case 'X_wins':
                message = 'Player X wins!';
                siteWrapper.classList.add('win-animation');
                scheduleRestart();
                break;
            case 'O_wins':
                message = 'Player O wins!';
                siteWrapper.classList.add('win-animation');
                scheduleRestart();
                break;
            case 'draw':
                message = "It's a draw!";
                siteWrapper.classList.add('win-animation');
                scheduleRestart();
                break;
            default:
                message = `Game status: ${currentGameData.status}`;
                break;
        }
        showMessage(message, false);
    }

    // Auto-restart helper
    function scheduleRestart() {
        setTimeout(() => {
            newGame(gameTypeSelect.value, difficultySelect.value);
        }, 3000);
    }

    // Show message in UI
    function showMessage(text, isError) {
        messageDiv.textContent = text;
        messageDiv.style.color = isError ? 'red' : 'black';
    }

    // Get CSRF token from cookie
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

    // Create a new game
    function newGame(gameType = 'two_player_offline', difficulty = 'hard') {
        fetch('/tictactoe/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ 
                game_type: gameType,
                difficulty: difficulty
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showMessage(data.error, true);
                return;
            }
            currentGameId = data.id;
            currentGameData = data;
            
            // Sync UI with loaded game type/difficulty
            gameTypeSelect.value = data.game_type;
            if (data.game_type === 'single_player_ai' || data.game_type === 'roguelike') {
                difficultyPanel.classList.remove('hidden');
                difficultySelect.value = data.difficulty;
            } else {
                difficultyPanel.classList.add('hidden');
            }
            
            updateGameState(data);
        })
        .catch(error => {
            showMessage('Error creating game: ' + error, true);
        });
    }

    // Reset button handler
    resetBtn.addEventListener('click', function() {
        newGame(gameTypeSelect.value, difficultySelect.value);
    });

    // Initialize the board
    initBoard();

    // Start initial game
    const initialId = boardDiv.dataset.initialId;
    if (initialId) {
        fetch(`/tictactoe/${initialId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                newGame(gameTypeSelect.value, difficultySelect.value);
            } else {
                currentGameId = data.id;
                currentGameData = data;
                
                // Sync UI with loaded game type/difficulty
                gameTypeSelect.value = data.game_type;
                if (data.game_type === 'single_player_ai' || data.game_type === 'roguelike') {
                    difficultyPanel.classList.remove('hidden');
                    difficultySelect.value = data.difficulty;
                } else {
                    difficultyPanel.classList.add('hidden');
                }
                
                updateGameState(data);
            }
        })
        .catch(() => newGame(gameTypeSelect.value, difficultySelect.value));
    } else {
        newGame(gameTypeSelect.value, difficultySelect.value);
    }
});