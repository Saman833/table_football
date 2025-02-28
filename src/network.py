import json
from websocket_server import WebsocketServer
import time


class Client:
    def __init__(self, client, index):
        self.client = client
        self.index = index

class ClientsService:
    def __init__(self):
        self.clients = []

    def add_client(self, client):
        index = 0
        if len(self.clients) > 0:
            index = 1 - self.clients[0].index
        self.clients.append(Client(client, index))
        for client in self.clients:
            print(client.client, client.index)

    def get_count(self):
        return len(self.clients)

    def remove_client(self, client):
        self.clients = [c for c in self.clients if c.client != client]

    def get_index(self, client):
        for c in self.clients:
            if c.client == client:
                return c.index
        return None

    def get_clients(self):
        return self.clients


class Network:
    def __init__(self, host='0.0.0.0', port=8080):
        self.server = WebsocketServer(host=host, port=port)
        self.clientService: ClientsService = ClientsService()
        self.moves_info = {
            'player1': [0, 0],
            'player2': [0, 0],
        }

        self.game_started = False

    def new_client(self, client, server):
        if self.clientService.get_count() >= 2:
            server.disconnect_client(client)
            return
        self.clientService.add_client(client)
        if self.clientService.get_count() == 2:
            self.game_started = True
        print(f"New client connected: {client['id']}")

    def client_left(self, client, server):
        self.clientService.remove_client(client)
        print(f"Client disconnected: {client['id']}")

    def message_received(self, client, server, message):
        if not self.game_started:
            return
        print(f"Message from client {client['id']}: {message} at {time.time()}")

        moves = json.loads(message)
        move = list(moves.values())
        player_index = self.clientService.get_index(client)

        if player_index == 0:
            self.moves_info['player1'] = move
        else:
            self.moves_info['player2'] = move

    def send_to_all(self, message):
        message = json.dumps(message)
        for c in self.clientService.get_clients():
            self.server.send_message(c.client, message)

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
