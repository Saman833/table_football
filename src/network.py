import json
from websocket_server import WebsocketServer
import time


class Network:
    def __init__(self, host='0.0.0.0', port=8080):
        self.server = WebsocketServer(host=host, port=port)
        self.clients = []
        self.moves_info = {
            'player1': [0, 0],
            'player2': [0, 0],
        }

        self.game_started = False

    def send_to_all(self, message):
        message = json.dumps(message)
        for c in self.clients:
            self.server.send_message(c, message)

    def new_client(self, client, server):
        if len(self.clients) >= 2:
            server.disconnect_client(client)
            return
        self.clients.append(client)
        if len(self.clients) == 2:
            self.game_started = True
        print(f"New client connected: {client['id']}")

    def client_left(self, client, server):
        self.clients.remove(client)
        print(f"Client disconnected: {client['id']}")

    def message_received(self, client, server, message):
        if not self.game_started:
            return
        print(f"Message from client {client['id']}: {message} at {time.time()}")

        moves = json.loads(message)
        move = list(moves.values())
        player_index = self.clients.index(client)

        if player_index == 0:
            self.moves_info['player1'] = move
        else:
            self.moves_info['player2'] = move

    def start_server(self):
        self.server.set_fn_new_client(self.new_client)
        self.server.set_fn_client_left(self.client_left)
        self.server.set_fn_message_received(self.message_received)

        self.server.run_forever()

    def get_moves(self):
        moves = self.moves_info
        self.moves_info = {
            'player1': [0, 0],
            'player2': [0, 0],
        }
        return moves

    def get_game_status(self):
        return self.game_started
