const websocket = new WebSocket('ws://localhost:8081/game');
const userIdentificationForm = document.getElementById('user-identification-form');
const gameBoard = document.getElementById('board');
const boardCells = gameBoard.getElementsByClassName('board-content-row-cell');
const sideMenu = document.getElementById('side-menu');

function popup(message, button, timeout) {
  // create the popup div

  const popup = document.createElement('div');
  popup.id = 'popup';
  const popupMessage = document.createElement('p');
  popupMessage.id = 'popup-message';
  popup.appendChild(popupMessage);
  popupMessage.innerText = message;
  document.body.appendChild(popup);
  if (button)
    button.disabled = true;

  setTimeout(() => {
    popup.classList.add('hidden');
    if (button)
      button.disabled = false;
  }, timeout);
}


websocket.onmessage = (event) => {
  // Parse the JSON message received from the server
  const data = JSON.parse(event.data);
  const type = data.type;
  switch (type) {
    case 'admin':
      console.log('You are now the admin');
      break;
    case 'joined-game':
      // Hide the user identification form
      userIdentificationForm.classList.add('hidden');
      // Show the game board
      gameBoard.classList.remove('hidden');
      // Show the side menu
      sideMenu.classList.remove('hidden');
      break;
    case 'available-formats':
      const formatsHTML = document.getElementById('available-formats');
      const availableFormats = data.formats;
      // formatsHTML is a ul element. Get the list of li elements
      const formatList = formatsHTML.getElementsByTagName('li');

      // Loop through the list of li elements
      for (let i = 0; i < formatList.length; i++) {
        const format = formatList[i];
        console.log(format);
        const formatName = format.getAttribute('data-format');
        // If the format is available, remove the disabled class
        console.log(availableFormats);
        if (availableFormats.includes(formatName)) {
          format.classList.remove('unavailable');
        }
        // Otherwise, add the disabled class
        else {
          format.classList.add('unavailable');
        }
      }
      break;
    case 'new-chat-message':
      // Add the new chat message to the chat box
      const chatBox = document.getElementById('chat-messages');
      const newMessage = document.createElement('div');
      newMessage.classList.add('chat-message');
      const sender = document.createElement('div');
      sender.classList.add('chat-message-sender');
      sender.innerText = data.sender;
      const message = document.createElement('div');
      message.classList.add('chat-message-content');
      message.innerText = data.message;
      newMessage.appendChild(sender);
      newMessage.appendChild(message);
      chatBox.appendChild(newMessage);
      chatBox.scrollTop = chatBox.scrollHeight;
      break;
    case 'game-data':
      // Update the game board
      const board = data.board;
      console.log(board);
      for (let i = 0; i < board.length; i++) {
        const row = board[i];
        for (let j = 0; j < row.length; j++) {
          const cell = row[j];
          const cellElement = document.querySelector(`[data-row="${i}"][data-col="${j}"]`);
          cellElement.innerText = cell;
        }
      }
      break;
    case 'game-won':
      // Show a popup with the winner's name
      popup(`${data.winner} has won the game! Congratulations!`, null, 5000);
      break;
    case 'game-started':
      popup(`The game has started! Good luck!`, null, 3000);
      break;
    case 'game-draw':
      popup(`The game is a draw!`, null, 5000);
      break;
    case 'player-joined':
      popup(`${data.player} has joined the game`, null, 2500);
      break;
    case 'player-left':
      popup(`${data.player} has left the game`, null, 2500);
      break;
    case 'whose-turn':
      popup(`${data.player}'s turn`, null, 2000);
      break;
    case 'error':
      const errorMessage = data.message;
      switch (errorMessage) {
        case 'game-already-started':
          popup('The game has already started', document.getElementById('start-button'), 2000);
          break;
        case 'not-enough-players':
          popup('Not enough players', document.getElementById('start-button'), 2000);
          break;
        case 'empty-message':
          popup('Please enter a message', document.getElementById('chat-input-send'), 2000);
          break;
        case 'turn-timed-out':
          popup('You took too long to play', null, 2000);
          if (!rollDiceButton.classList.contains('hidden')) {
            rollDiceButton.classList.add('hidden');
            rollDiceButton.disabled = true;
          }
          break;
        default:
          popup('An error has occurred: ' + errorMessage, document.getElementById('start-button'), 2000);
          break;
      }
      break;
    default:
      console.log('Unknown message type: ' + type);
      break;
      
  }
}




websocket.onopen = () => {
  // Show a floating form to ask the user for their name and format  // Hide the game board
  // Send a message to the server to join the game
  websocket.send(JSON.stringify({
    type: 'join',
  }));
}


for (let i = 0; i < boardCells.length; i++) {
  boardCells[i].addEventListener('click', () => {
    const row = boardCells[i].getAttribute('data-row');
    const col = boardCells[i].getAttribute('data-col');
    websocket.send(JSON.stringify({
      type: 'move',
      row: row,
      col: col,
    }));
  });
}

document.getElementById('user-identification-form-content-submit-button').addEventListener('click', () => {
  // Get the name and format from the form
  const nameInput = document.getElementById('user-identification-form-content-name-input').value;
  const formats = document.getElementById('available-formats').getElementsByTagName('li');
  let formatInput = '';
  for (let i = 0; i < formats.length; i++) {
    const format = formats[i];
    if (format.classList.contains('selected')) {
      formatInput = format.getAttribute('data-format');
    }
  }

  // If the user didn't enter a name, don't do anything
  if (nameInput === '') {
    popup('Please enter a name', document.getElementById('user-identification-form-content-submit-button'), 2000);
    // focus the name input
    document.getElementById('user-identification-form-content-name-input').focus();
    return;
  }
  // If the user didn't select a format, don't do anything
  if (formatInput === '') {
    popup('Please select a format', document.getElementById('user-identification-form-content-submit-button'), 2000);
    return;
  }
  websocket.send(JSON.stringify({
    type: 'join-game',
    name: nameInput,
    format: formatInput,
  }));
});

let selectedFormat = null;
const formats = document.getElementsByClassName('format');
for (let i = 0; i < formats.length; i++) {
  formats[i].addEventListener('click', () => {
    if (formats[i].classList.contains('unavailable')) {
      return;
    }
    const formatName = formats[i].getAttribute('data-format');
    websocket.send(JSON.stringify({
      type: 'set-format',
      format: formatName,
    }));
    if (selectedFormat !== null) {
      selectedFormat.classList.remove('selected');
    }
    selectedFormat = formats[i];
    selectedFormat.classList.add('selected');
  });
}


const menuButtons = document.querySelectorAll('.menu-button');

document.getElementById('chat-button').addEventListener('click', () => {
  // Show or hide the chat box
  document.getElementById('chat-panel').classList.toggle('hidden');
  menuButtons.forEach(button => {
    if (button.id !== 'chat-button') {

      if (button.classList.contains('active-button')) {
        button.classList.remove('active-button');
      }
    }
  });
  document.getElementById('chat-button').classList.toggle('active-button');
});

document.getElementById('start-button').addEventListener('click', () => {
  // Send a message to the server to start the game
  websocket.send(JSON.stringify({
    type: 'start-game',
  }));
});

document.getElementById('chat-input-send').addEventListener('click', () => {
  // Send a message to the server to send a chat message
  websocket.send(JSON.stringify({
    type: 'sent-chat-message',
    message: document.getElementById('chat-input-text').value,
  }));
  // Clear the chat input
  document.getElementById('chat-input-text').value = '';
});

// if element chat-input-text is selected and enter is pressed, send the message
document.getElementById('chat-input-text').addEventListener('keydown', (event) => {
  if (event.key === 'Enter') {
    if (document.getElementById('chat-input-send').disabled) {
      return;
    }
    websocket.send(JSON.stringify({
      type: 'sent-chat-message',
      message: document.getElementById('chat-input-text').value,
    }));
    // Clear the chat input
    document.getElementById('chat-input-text').value = '';
  }
}
);