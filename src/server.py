import json
import threading
from math import gamma

from websocket_server import WebsocketServer
import time
from game_engine import Game, Player



class WebSocketServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.server = WebsocketServer(host=host, port=port)
        self.clients = []
        self.game = Game()
        self.moves_info = {
            "player1": [0, 0],
            "player2": [0, 0]
        }

        self.game_started = False

    def send_to_all(self, message):
        message = json.dumps(message)
        for c in self.clients:
            self.server.send_message(c, message)

    def new_client(self, client, server):
        if len(self.clients) > 2:
            server.disconnect_client(client)
            return
        self.clients.append(client)
        if len(self.clients) == 2:
            self.game_started = True
            self.send_to_all(
                self.game.get_updates()
            )
        print(f"New client connected: {client['id']}")

    def client_left(self, client, server):
        self.clients.remove(client)
        print(f"Client disconnected: {client['id']}")
        #self.stop_game()

    def stop_game(self):
        self.send_to_all("Game Stopped")
        self.server.server_close()

    def message_received(self, client, server, message):
        if not self.game_started:
            return
        print(f"Message from client {client['id']}: {message} at {time.time()}")

        self.update_moves(client, message)
        # TODO: pass data to Saman
        # time.sleep(10)
        # print(f"Stopped sleeping from client {client['id']}")
        self.send_to_all(
            self.game.get_updates()
        )

    def game_loop(self):
        while True:
            if self.game_started:
                self.game.game_step(self.moves_info)
                self.moves_info = {
                    "player1": [0, 0],
                    "player2": [0, 0]
                }
                self.send_to_all(self.game.get_updates())
            time.sleep(0.01)

    def update_moves(self, client, message):
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

        loop_thread = threading.Thread(target=self.game_loop, daemon=True)
        loop_thread.start()

        self.server.run_forever()


def main():
    ws_server = WebSocketServer()
    ws_server.start_server()


if __name__ == "__main__":
    main()
