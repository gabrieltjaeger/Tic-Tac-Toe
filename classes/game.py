from .exceptions import GameAlreadyStarted, GamePaused, MaxPlayersReached, NotEnoughPlayers
from .player import Player
from random import randint


class Game: #TicTacToe
    def __init__(self, server, players: list = [], available_formats: dict = None):
        self.server = server
        self.players = players
        self.MAX_PLAYERS = 8
        self.MIN_PLAYERS = 2
        self.board = [['' for _ in range(3)] for _ in range(3)]
        self.turn = 0
        self.current_player = None
        self.started = False
        self.available_formats = {format: True for format in Player.FORMATS} if available_formats is None else available_formats

    def status(self) -> dict:
        return self.board

    def move(self, player: Player, row: int, col: int):
        if not self.started:
            raise Exception('Game not started')
        if not self.is_turn(player.user.websocket):
            raise Exception('Not your turn')
        if self.get_cell(row, col) != '':
            raise Exception('Cell already taken')
        self.set_cell(row, col, player.format)


    def check_win(self, format: str) -> bool:
        for i in range(3):
            if self.board[i][0] == self.board[i][1] == self.board[i][2] == format:
                return True
            if self.board[0][i] == self.board[1][i] == self.board[2][i] == format:
                return True
        if self.board[0][0] == self.board[1][1] == self.board[2][2] == format:
            return True
        if self.board[0][2] == self.board[1][1] == self.board[2][0] == format:
            return True
        return False


    def get_cell(self, row: int, col: int):
        return self.board[row][col]

    def set_cell(self, row: int, col: int, value: str):
        self.board[row][col] = value


    def new_player(self, player: Player):
        if len(self.players) >= self.MAX_PLAYERS:
            raise MaxPlayersReached(self.MAX_PLAYERS)
        self.players.append(player)
        self.available_formats[player.format] = False
        
    def remove_player(self, websocket):
        player = self.get_player(websocket)
        self.available_formats[player.format] = True
        self.turn -= 1
        self.players.remove(player)

    def is_turn(self, websocket) -> bool:
        current_player = self.get_whose_turn()
        if current_player is None:
            return False
        return current_player.user.websocket == websocket

    def is_player(self, websocket) -> bool:
        for player in self.players:
            if player.user.websocket == websocket:
                return True
        return False

    def start(self):
        if len(self.players) < self.MIN_PLAYERS:
            raise NotEnoughPlayers(self.MIN_PLAYERS)
        if self.started:
            raise GameAlreadyStarted()
        if self.current_player is None:
            self.current_player = self.players[randint(0, len(self.players) - 1)]
        self.board = [['' for _ in range(3)] for _ in range(3)]
        self.turn = 0
        self.started = True

    def stop(self):
        self.started = False

    def reset(self):
        self.stop()
        self.board = None
        self.current_player = None
        self.turn = 0

    
    def get_player(self, websocket) -> Player:
        for player in self.players:
            if player.user.websocket == websocket:
                return player

    
    def update_current_player(self):
        self.current_player = self.players[(self.players.index(self.current_player) + 1) % len(self.players)]

    def get_whose_turn(self) -> Player:
        return self.current_player

    def next_turn(self):
        self.turn += 1
        if self.turn >= 9:
            self.started = False
            return False
        self.update_current_player()
        return True

    def get_available_formats(self):
        return [format for format, available in self.available_formats.items() if available]
    
    def get_capacity(self) -> str:
        return f'{len(self.players)}/{self.MAX_PLAYERS}'
