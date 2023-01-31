# Import the http.server module
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import sys

SERVER_ADDRESS = ('', 3389)


# Create a custom request handler that serves the index.html file and the
# JavaScript and CSS files in their respective folders
class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        if path == 'index.html':
            type = 'text/html'
        elif path.startswith('/css/'):
            type = 'text/css'
        elif path.startswith('/script/'):
            type = 'text/javascript'
        elif path.startswith('/img/'):
            if path.endswith('.png'):
                type = 'image/png'
            elif path.endswith('.jpg'):
                type = 'image/jpg'
            elif path.endswith('.svg'):
                type = 'image/svg+xml'
            else:
                type = 'image'
        else:
            if not path == '/':
                self.send_error(404)
                return
            path = 'index.html'
            type = 'text/html'

        self.send_response(200)
        self.send_header('Content-type', type)
        self.end_headers()
        if path.startswith('/'):
            path = path[1:]

        current_directory = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(current_directory, path)

        with open(path, 'rb') as file:
            self.wfile.write(file.read())
            
        
            

# Create the server
server = HTTPServer(SERVER_ADDRESS, RequestHandler)

# Run the server
server.serve_forever()

