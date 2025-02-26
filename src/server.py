import json
import threading
from math import gamma

from websocket_server import WebsocketServer
import time
from game_engine import Game, Player
from network import Network



class Server:
    def __init__(self, host='0.0.0.0', port=8080):
        self.network = Network(host=host, port=port)
        self.clients = []
        self.game = Game()

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
