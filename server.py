import json

from websocket_server import WebsocketServer
import threading
import time
from object import Object


def start_game():
    return True

player1 = Object('{"x": 200, "y": 200}')
player2 = Object('{"x": 500, "y": 200}')
ball = Object('{"x": 350, "y": 200}')

class WebSocketServer:
    def __init__(self, host='0.0.0.0', port=8080):
        self.server = WebsocketServer(host=host, port=port)
        self.server.set_fn_new_client(self.new_client)
        self.server.set_fn_client_left(self.client_left)
        self.server.set_fn_message_received(self.message_received)
        self.clients = []
        self.thread = threading.Thread(target=self.run_server)

        self.game_started = False

    def send_to_all(self, message):
        for c in self.clients:
            self.server.send_message(c, message)

    def new_client(self, client, server):
        if len(self.clients) > 2:
            server.disconnect_client(client)
            return
        self.clients.append(client)
        if len(self.clients) == 2:
            self.game_started = start_game()

            player1 = Object('{"x": 200, "y": 200}')
            player2 = Object('{"x": 500, "y": 200}')
            ball = Object('{"x": 350, "y": 200}')

            self.send_to_all(
                self.format_response(player1, player2, ball)
            )
        print(f"New client connected: {client['id']}")

    def client_left(self, client, server):
        self.clients.remove(client)
        print(f"Client disconnected: {client['id']}")
        self.stop_game()

    def stop_game(self):
        self.send_to_all("Game Stopped")
        self.server.server_close()

    def message_received(self, client, server, message):
        if not self.game_started:
            return
        print(f"Message from client {client['id']}: {message} at {time.time()}")

        player_index = self.clients.index(client)
        player = Object(message)
        response = self.change(player_index, player)

        # TODO: pass data to Saman
        # time.sleep(10)
        # print(f"Stopped sleeping from client {client['id']}")
        self.send_to_all(response)

    def change(self, player_index, player):


        if player_index == 0:
            player1.update(player.x, player.y)
        else:
            player2.update(player.x, player.y)

        return self.format_response(player1, player2, ball)

    def format_response(self, player1, player2, ball):
        return json.dumps({
            "player1": player1.to_json(),
            "player2": player2.to_json(),
            "ball": ball.to_json()
        })

    def run_server(self):
        self.server.run_forever()


def main():
    ws_server = WebSocketServer()
    ws_server.run_server()


if __name__ == "__main__":
    main()

# "x y"
# "x1 y1 x2 y2 x3 y3"
