import asyncio
import json
import websockets
import threading
from .game import Game
from .player import Player
from .user import User
from .exceptions import GameAlreadyStarted, GamePaused, MaxPlayersReached, NotEnoughPlayers
from time import sleep




class Server:
    def __init__(self, host, port) -> None:
        self.HOST = host
        self.PORT = port
        self.connected_clients = []
        self.admin = None
        self.game = Game(self)
        self.formats = {}  # websocket: format


    def catch_game_exceptions(func):
        async def wrapper(*args, **kwargs):
            try:
                await func(*args, **kwargs)
            except GameAlreadyStarted:
                await args[1].send(json.dumps({'type': 'error', 'message': 'Game already started'}))
            except GamePaused:
                await args[1].send(json.dumps({'type': 'error', 'message': 'Game paused'}))
            except MaxPlayersReached:
                await args[1].send(json.dumps({'type': 'error', 'message': 'Max players reached'}))
            except NotEnoughPlayers:
                await args[1].send(json.dumps({'type': 'error', 'message': 'Not enough players'}))
            except websockets.exceptions.ConnectionClosed:
                await args[0].disconnect_client(args[1])
            except Exception as e:
                print(e, type(e), e.args, e.with_traceback, e.with_traceback())
                message = str(e)
                await args[1].send(json.dumps({'type': 'error', 'message': message}))
        return wrapper

    @catch_game_exceptions
    async def connect_client(self, websocket):
        if self.admin is None:
            self.admin = websocket
            # Send a message to the client that they are the admin
            await websocket.send(json.dumps({'type': 'admin'}))

        self.connected_clients.append(websocket)
        print(f'Client {websocket.remote_address} connected to the server.')
        await websocket.send(json.dumps({'type': 'available-formats', 'formats': self.game.get_available_formats()}))

    @catch_game_exceptions
    async def finish_turn(self, websocket):
        if not self.game.is_turn(websocket):
            return
        self.game.finish_turn()
        await self.broadcast(json.dumps({'type': 'turn-finished'}))
        await self.send_whose_turn()
      
    @catch_game_exceptions
    async def disconnect_client(self, websocket):
        self.connected_clients.remove(websocket)
        print(f'Client {websocket.remote_address} disconnected from the server.')

        if websocket == self.admin:
            self.admin = None
            if len(self.connected_clients) > 0:
                self.admin = self.connected_clients[0]
                await self.admin.send(json.dumps({'type': 'admin'}))
            print('Admin disconnected.')

        if websocket in self.game.players:
            await self.broadcast(json.dumps({'type': 'player-left', 'player': self.game.get_player(websocket).user.name}))
            self.game.remove_player(websocket)
            players = self.game.players
            available_formats = self.game.available_formats
            self.game = Game(self, players, available_formats)
            await self.broadcast(json.dumps({'type': 'game-data', "board": self.game.status()}))
            print(f'Client {websocket.remote_address} disconnected from the game.')
            return
        

    @catch_game_exceptions
    async def listener(self, websocket):
        await self.connect_client(websocket)

        try:
            while True:
                # Waits for a message from the client
                DATA = json.loads(await websocket.recv())

                await self.handle_message(websocket, DATA)
        except websockets.exceptions.ConnectionClosed:
            await self.disconnect_client(websocket)
        finally:
            print(f'Client {websocket.remote_address} disconnected.')

    @catch_game_exceptions
    async def join(self, websocket):
        print(f'Client {websocket.remote_address} joined the server.')

    @catch_game_exceptions
    async def join_game(self, websocket, data):
        NAME = str(data['name'])
        FORMAT = str(data['format'])
        NEW_PLAYER = Player(User(websocket, NAME), FORMAT)
        self.game.new_player(NEW_PLAYER)

        print(
            f'Client {websocket.remote_address} joined the game as {NEW_PLAYER} and chose the format {NEW_PLAYER.format}.')
        print(f'Game capacity: {self.game.get_capacity()}')
        await websocket.send(json.dumps({'type': 'joined-game'}))
        await self.broadcast(json.dumps({'type': 'player-joined', 'player': NEW_PLAYER.user.name}))

    @catch_game_exceptions
    async def handle_message(self, websocket, data):
        TYPE = data['type']

        # These constants shall be moved to another part of the code in the future
        ALLOWED_NOT_PLAYER_TYPES = [
            'join', 'join-game', 'get-available-formats', 'set-format']
        PLAYER_TYPES = ['move']
        ADMIN_TYPES = ['start-game', 'pause-game', 'resume-game', 'reset-game']
        ALLOWED_OUT_OF_TURN_TYPES = ['sent-chat-message']
        TYPES = PLAYER_TYPES + ADMIN_TYPES + ALLOWED_NOT_PLAYER_TYPES + ALLOWED_OUT_OF_TURN_TYPES

        if TYPE not in TYPES:
            await websocket.send(json.dumps({'type': 'error', 'message': 'Invalid message type.'}))
            return
        
        if TYPE in PLAYER_TYPES and not self.game.is_player(websocket):
            await websocket.send(json.dumps({'type': 'error', 'message': 'You are not a player.'}))
            return

        if TYPE in ADMIN_TYPES and websocket != self.admin:
            await websocket.send(json.dumps({'type': 'error', 'message': 'You are not the admin.'}))
            return
        
        if TYPE in PLAYER_TYPES and not self.game.started:
            await websocket.send(json.dumps({'type': 'error', 'message': 'The game has not started yet.'}))
            return
        
        if TYPE in PLAYER_TYPES and not self.game.is_turn(websocket):
            await websocket.send(json.dumps({'type': 'error', 'message': 'It is not your turn.'}))
            return
        
        PLAYER = self.game.get_player(websocket)

        match TYPE:
            case 'join':
                await self.join(websocket)
            case 'join-game':
                await self.join_game(websocket, data)
            case 'get-available-formats':
                await self.send_available_formats(websocket)
            case 'set-format':
                self.game.available_formats[data['format']] = False
                if websocket in self.formats:
                    self.game.available_formats[self.formats[websocket]] = True
                self.formats[websocket] = data['format']
                print(self.game.available_formats)
                await self.send_available_formats()
            case 'start-game':
                self.game.start()
                print('Game started')
                await self.broadcast(json.dumps({'type': 'game-started'}))
                await self.broadcast(json.dumps({'type': 'game-data', "board": self.game.status()}))
                await self.send_whose_turn() 
            case 'sent-chat-message':
                new_message = data['message']
                if new_message == '':
                    await self.send_error_message(websocket, 'empty-message')
                    return
                sender = str(self.game.get_player(websocket).user.name)
                await self.broadcast(json.dumps({'type': 'new-chat-message', 'sender': sender, 'message': data['message']}))
            case 'move':
                ROW = int(data['row'])
                COL = int(data['col'])
                await self.move(PLAYER.user.websocket, PLAYER, ROW, COL)

    @catch_game_exceptions
    async def move(self, websocket, player, row, col):
        self.game.move(player, row, col)
        win = self.game.check_win(player.format)
        await self.broadcast(json.dumps({'type': 'game-data', "board": self.game.status()}))
        if win:
            self.game.stop()
            await self.broadcast(json.dumps({'type': 'game-won', 'winner': str(player.user.name)}))
            return
        draw = not self.game.next_turn()
        if draw:
            self.game.stop()
            await self.broadcast(json.dumps({'type': 'game-draw'}))
            return
        await self.send_whose_turn()
        
    @catch_game_exceptions
    async def send_whose_turn(self):
        whose_turn: Player = self.game.get_whose_turn()
        print(f'Whose turn: {whose_turn.user.websocket.remote_address}')
        await self.broadcast(json.dumps({'type': 'whose-turn', 'player': str(whose_turn.user.name)}))
        try:
            await whose_turn.user.websocket.send(json.dumps({'type': 'your-turn'}))
        except websockets.exceptions.ConnectionClosed:
            await self.disconnect_client(whose_turn.user.websocket)

    async def send_error_message(self, websocket, message):
        await websocket.send(json.dumps({'type': 'error', 'message': message}))

    async def send_available_formats(self, websocket=None):
        message = json.dumps(
            {'type': 'available-formats', 'formats': self.game.get_available_formats()})
        if websocket is None:
            print('Sending available formats to all clients')
            await self.broadcast(message)
            return
        print(f'Sending available formats to {websocket.remote_address}')
        await websocket.send(message)

    async def broadcast(self, message):
        # Send a message to all connected clients
        for websocket in self.connected_clients:
            await websocket.send(message)

    async def start_server(self):
        # Start the server
        start_server = websockets.serve(self.listener, self.HOST, self.PORT)
        await start_server
        print('Server started')
        await asyncio.Future()

    def run(self):
        asyncio.run(self.start_server())
