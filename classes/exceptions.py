class GameAlreadyStarted(Exception):
    def __init__(self):
        self.message = 'The game has already started.'


class MaxPlayersReached(Exception):
    def __init__(self, max_players):
        self.max_players = max_players
        self.message = f'The maximum number of {self.max_players} players has already been reached.'


class NotEnoughPlayers(Exception):
    def __init__(self, min_players):
        self.min_players = min_players
        self.message = f'Not enough players to start the game. The minimum number of players is {self.min_players}.'

class GamePaused(Exception):
    def __init__(self):
        self.message = 'The game is paused.'

class AlreadyOwned(Exception):
    pass

class NotEnoughMoney(Exception):
    def __init__(self, price):
        self.price = price

    def __str__(self):
        return f'Not enough money. You need {self.price}.'
    
class NotOwned(Exception):
    pass

class HasBuildings(Exception):
    pass

class CannotPayYourself(Exception):
    pass