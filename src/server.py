import json
import threading
from math import gamma

from websocket_server import WebsocketServer
import time
from game_engine import Game, Player
from network import Network

player1 = Player(color="red", x_coordinate=200, y_coordinate=200, score=0, radius=20, name="Player1", speed=[7, 7])
player2 = Player(color="blue", x_coordinate=200, y_coordinate=500, score=0, radius=20, name="Player2", speed=[7, 7])


class Server:
    def __init__(self, host='0.0.0.0', port=8080):
        self.network = Network(host=host, port=port)
        self.clients = []
        self.game = Game(player1, player2)

        self.game_started = False

    def game_loop(self):
        while True:
            if self.network.get_game_status():
                moves_info = self.network.get_moves()
                self.game.game_step(moves_info)
                self.network.send_to_all(self.game.get_updates())
            time.sleep(0.01)

    def start_server(self):
        loop_thread = threading.Thread(target=self.network.start_server, daemon=True)
        loop_thread.start()
        self.game_loop()


def main():
    ws_server = Server()
    ws_server.start_server()


if __name__ == "__main__":
    main()
