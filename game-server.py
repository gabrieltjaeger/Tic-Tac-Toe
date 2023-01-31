from classes.server import Server

HOST: str = ''
PORT: int = 8081


def main():
    server = Server(HOST, PORT)
    server.run()


if __name__ == '__main__':
    main()
