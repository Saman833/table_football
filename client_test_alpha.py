import pygame
import json
import threading
import time
import sys
import socket
import base64
import random
import struct
import hashlib

# Game settings
WIDTH, HEIGHT = 800, 600
PADDLE_RADIUS = 40
BALL_RADIUS = 20

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
GREEN = (0, 255, 0)

class WebSocketClient:
    def __init__(self, url):
        parts = url.replace('ws://', '').split(':')
        self.host = parts[0]
        self.port = int(parts[1]) if len(parts) > 1 else 8080
        self.socket = None
        self.connected = False
        self.callback = None
        self.running = False
        self.thread = None

    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))

            # Generate WebSocket key - MUST be properly formatted for handshake
            key = base64.b64encode(bytes([random.randint(0, 255) for _ in range(16)])).decode()

            # Send handshake
            handshake = (
                f"GET / HTTP/1.1\r\n"
                f"Host: {self.host}:{self.port}\r\n"
                f"Upgrade: websocket\r\n"
                f"Connection: Upgrade\r\n"
                f"Sec-WebSocket-Key: {key}\r\n"
                f"Origin: http://{self.host}:{self.port}\r\n"  # Added Origin header
                f"Sec-WebSocket-Version: 13\r\n\r\n"
            )

            self.socket.send(handshake.encode())

            # Validate server response
            response = b""
            while b"\r\n\r\n" not in response:
                chunk = self.socket.recv(4096)
                if not chunk:
                    raise ConnectionError("Connection closed during handshake")
                response += chunk

            if b"101 Switching Protocols" in response:
                self.connected = True
                self.running = True
                self.thread = threading.Thread(target=self._receive_loop)
                self.thread.daemon = True
                self.thread.start()
                print("WebSocket connected successfully")
                return True
            else:
                print(f"WebSocket handshake failed: {response.decode('utf-8', errors='replace')}")
                return False

        except Exception as e:
            print(f"Connection error: {e}")
            if self.socket:
                self.socket.close()
            return False

    def _receive_loop(self):
        try:
            buffer = bytearray()

            while self.running:
                chunk = self.socket.recv(4096)
                if not chunk:
                    raise ConnectionError("Connection closed by server")

                buffer.extend(chunk)

                # Process complete frames in buffer
                while len(buffer) >= 2:
                    # Parse header
                    fin = (buffer[0] & 0x80) != 0
                    opcode = buffer[0] & 0x0F
                    mask = (buffer[1] & 0x80) != 0
                    payload_len = buffer[1] & 0x7F

                    header_length = 2

                    # Extended payload length
                    if payload_len == 126:
                        if len(buffer) < 4:
                            break  # Need more data
                        payload_len = struct.unpack("!H", buffer[2:4])[0]
                        header_length += 2
                    elif payload_len == 127:
                        if len(buffer) < 10:
                            break  # Need more data
                        payload_len = struct.unpack("!Q", buffer[2:10])[0]
                        header_length += 8

                    # Masking key
                    if mask:
                        if len(buffer) < header_length + 4:
                            break  # Need more data
                        masking_key = buffer[header_length:header_length+4]
                        header_length += 4

                    # Check if complete frame is available
                    if len(buffer) < header_length + payload_len:
                        break  # Need more data

                    # Extract and process payload
                    payload = buffer[header_length:header_length+payload_len]

                    # Unmask if needed
                    if mask:
                        unmasked = bytearray(payload_len)
                        for i in range(payload_len):
                            unmasked[i] = payload[i] ^ masking_key[i % 4]
                        payload = unmasked

                    # Handle close frames
                    if opcode == 0x8:  # Close frame
                        self.close()
                        return

                    # Handle data frames
                    if opcode == 0x1:  # Text frame
                        message = payload.decode('utf-8', errors='replace')
                        if self.callback:
                            self.callback(message)

                    # Remove processed frame from buffer
                    buffer = buffer[header_length+payload_len:]

        except ConnectionError as e:
            print(f"Connection closed: {e}")
        except Exception as e:
            print(f"Receive error: {e}")
        finally:
            self.connected = False
            print("WebSocket connection closed")

    def send(self, message):
        """Send a text message with proper masking"""
        if not self.connected:
            return False

        try:
            data = message.encode('utf-8')
            length = len(data)

            # Create header
            frame = bytearray()

            # Byte 1: FIN + opcode (0x81 for text frame)
            frame.append(0x81)

            # Byte 2: Masked flag + payload length
            # IMPORTANT: The mask bit (0x80) must be set for client-to-server messages
            if length < 126:
                frame.append(0x80 | length)  # Set mask bit (0x80) and include length
            elif length < 65536:
                frame.append(0x80 | 126)  # Set mask bit with extended length indicator
                frame.extend(struct.pack('!H', length))  # 2-byte length
            else:
                frame.append(0x80 | 127)  # Set mask bit with extended length indicator
                frame.extend(struct.pack('!Q', length))  # 8-byte length

            # Generate a random mask key
            mask = bytes([random.randint(0, 255) for _ in range(4)])
            frame.extend(mask)

            # Mask the payload
            masked_data = bytearray(length)
            for i in range(length):
                masked_data[i] = data[i] ^ mask[i % 4]

            # Add the masked payload
            frame.extend(masked_data)

            # Send everything in one call to avoid fragmentation
            self.socket.sendall(frame)
            return True

        except Exception as e:
            print(f"Send error: {e}")
            self.connected = False
            return False

    def set_callback(self, callback):
        self.callback = callback

    def close(self):
        if not self.connected:
            return

        try:
            # Send close frame with proper masking
            close_frame = bytearray()
            close_frame.append(0x88)  # FIN + Close opcode
            close_frame.append(0x82)  # Masked + payload length 2

            # Random mask
            mask = bytes([random.randint(0, 255) for _ in range(4)])
            close_frame.extend(mask)

            # Status code 1000 (normal closure) - properly masked
            status_code = bytearray([0x03, 0xe8])  # 1000 in bytes
            for i in range(2):
                close_frame.append(status_code[i] ^ mask[i % 4])

            self.socket.send(close_frame)
        except:
            pass

        self.running = False
        self.connected = False

        try:
            self.socket.close()
        except:
            pass


class AirHockeyClient:
    def __init__(self, server_url="ws://localhost:8080"):
        # Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Air Hockey Game")
        self.clock = pygame.time.Clock()

        # Game state
        self.player1 = {"x": 200, "y": 200}
        self.player2 = {"x": 500, "y": 200}
        self.ball = {"x": 350, "y": 200}

        # Connection state
        self.connected = False
        self.player_num = None  # Will be 0 (player1) or 1 (player2)
        self.server_url = server_url
        self.ws = None
        self.game_started = False

        # Message handling
        self.lock = threading.Lock()

    def on_message(self, message):
        try:
            print(f"Received: {message}")

            # Server might send "Game Stopped" as a string
            if message == "Game Stopped":
                print("Game stopped by server")
                self.game_started = False
                return

            # Parse the game state
            data = json.loads(message)

            with self.lock:
                # Check if we need to parse nested JSON strings
                if "player1" in data:
                    # Fix: Parse the nested JSON string for player1
                    if isinstance(data["player1"], str):
                        self.player1 = json.loads(data["player1"])
                    else:
                        self.player1 = data["player1"]

                # Handle both versions of the key (with and without typo)
                if "player2" in data:
                    # Fix: Parse the nested JSON string for player2
                    if isinstance(data["player2"], str):
                        self.player2 = json.loads(data["player2"])
                    else:
                        self.player2 = data["player2"]
                elif "plater2" in data:  # Handle original typo from server
                    # Fix: Parse the nested JSON string for plater2
                    if isinstance(data["plater2"], str):
                        self.player2 = json.loads(data["plater2"])
                    else:
                        self.player2 = data["plater2"]

                if "ball" in data:
                    # Fix: Parse the nested JSON string for ball
                    if isinstance(data["ball"], str):
                        self.ball = json.loads(data["ball"])
                    else:
                        self.ball = data["ball"]

                # Check for status
                if "status" in data:
                    if data["status"] == "connected" and "player_id" in data:
                        self.player_num = data["player_id"] - 1
                        print(f"Server assigned player number: {self.player_num + 1}")
                    elif data["status"] == "game_update":
                        self.game_started = True

            # If we don't have a player_num yet, determine it
            if self.player_num is None and not hasattr(self, 'player_num'):
                # Default behavior if server doesn't specify - player 1 connects first
                self.player_num = 0
                print(f"Assuming player number: {self.player_num + 1}")

            # Set game started when we receive game state
            if not self.game_started and "ball" in data:
                self.game_started = True
                print("Game started!")

        except json.JSONDecodeError:
            print(f"Error parsing message: {message}")
        except Exception as e:
            print(f"Message processing error: {e}")

    def connect_to_server(self):
        """Connect to WebSocket server"""
        print(f"Connecting to {self.server_url}...")
        self.ws = WebSocketClient(self.server_url)
        self.ws.set_callback(self.on_message)
        if self.ws.connect():
            self.connected = True
            print("Connected to server")
        else:
            print("Failed to connect to server")

    def send_player_update(self, x, y):
        """Send player position update to server"""
        if self.connected:
            message = json.dumps({"x": x, "y": y})
            if not self.ws.send(message):
                print("Failed to send update to server")
                self.connected = False

    def run_game(self):
        """Main game loop"""
        self.connect_to_server()

        # Wait for connection
        connection_timeout = 5  # seconds
        start_time = time.time()
        while not self.connected and time.time() - start_time < connection_timeout:
            time.sleep(0.1)

        if not self.connected:
            print("Could not connect to server")
            font = pygame.font.Font(None, 36)
            self.screen.fill(WHITE)
            text = font.render("Could not connect to server", True, RED)
            self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
            pygame.display.flip()
            time.sleep(3)
            pygame.quit()
            return

        # Main game loop
        running = True
        my_x, my_y = 200, 200  # Default starting position

        while running:
            # Handle Pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Clear the screen
            self.screen.fill(WHITE)

            # Draw center line and goal areas
            pygame.draw.line(self.screen, GRAY, (WIDTH // 2, 0), (WIDTH // 2, HEIGHT), 2)
            pygame.draw.circle(self.screen, GRAY, (WIDTH // 2, HEIGHT // 2), 50, 2)

            # Handle player movement
            if self.connected:
                # Get mouse position for paddle control
                mouse_x, mouse_y = pygame.mouse.get_pos()

                # Always update position based on mouse movement
                my_x = max(PADDLE_RADIUS, min(mouse_x, WIDTH - PADDLE_RADIUS))
                my_y = max(PADDLE_RADIUS, min(mouse_y, HEIGHT - PADDLE_RADIUS))

                # Send position update
                self.send_player_update(my_x, my_y)

            # Draw game elements based on current state
            with self.lock:
                # Draw player 1 paddle
                pygame.draw.circle(self.screen, RED, (int(self.player1["x"]), int(self.player1["y"])), PADDLE_RADIUS)

                # Draw player 2 paddle
                pygame.draw.circle(self.screen, BLUE, (int(self.player2["x"]), int(self.player2["y"])), PADDLE_RADIUS)

                # Draw ball
                pygame.draw.circle(self.screen, BLACK, (int(self.ball["x"]), int(self.ball["y"])), BALL_RADIUS)

            # Draw status text
            font = pygame.font.Font(None, 36)
            if not self.game_started:
                status = "Waiting for another player..."
                text = font.render(status, True, BLACK)
                self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 20))
            else:
                if self.player_num == 0:
                    status = "You are Player 1 (Red)"
                else:
                    status = "You are Player 2 (Blue)"
                text = font.render(status, True, BLACK)
                self.screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 20))

            # Display connection status
            status_color = GREEN if self.connected else RED
            conn_text = font.render("Connected" if self.connected else "Disconnected", True, status_color)
            self.screen.blit(conn_text, (WIDTH - conn_text.get_width() - 10, 10))

            # Update the display
            pygame.display.flip()
            self.clock.tick(60)

        # Clean up
        if self.connected and self.ws:
            self.ws.close()
        pygame.quit()


if __name__ == "__main__":
    # Allow command line argument for server URL
    server_url = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8080"
    client = AirHockeyClient(server_url)
    client.run_game()