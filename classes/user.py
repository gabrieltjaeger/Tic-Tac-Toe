class User:
    def __init__(self, websocket, name = None):
        self.websocket = websocket
        self.name = name

    def __eq__(self, other):
        return self.websocket == other.websocket