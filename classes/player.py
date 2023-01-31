from .user import User


class Player:
    FORMATS = ['X', 'O']
    def __init__(self, user: User, format: str) -> None:
        if format not in Player.FORMATS:
            raise ValueError('Format not available')
        self.user = user
        self._format = format

    @property
    def format(self) -> str:
        return self._format

    @format.setter
    def format(self, format) -> None:
        if format in self.FORMAT:
            self._format = format
        else:
            raise ValueError('Format not available')

    def __str__(self) -> str:
        return f'Player {self.user.name}'
    
    # If a list of players is consulted for a player, to know if a player is in the list, the __eq__ method is called
    def __eq__(self, other) -> bool:
        return self.user.websocket == other
    
    def __hash__(self) -> int:
        return hash(self.user)
    
    def __repr__(self) -> str:
        return self.__str__()

