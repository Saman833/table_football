import pygame
import json
import websocket
import sys
import threading
import time
import os

# Enable this for more verbose WebSocket logging
# websocket.enableTrace(False)

class MinimalAirHockeyClient:
    def __init__(self):
        print("Initializing client...")
        self.server_url = "ws://localhost:8080"
        self.connected = False
        self.game_state = None
        self.running = True

        # Store the last message for debugging
        self.last_message = None

        # Lock for thread-safe access to game state
        self.state_lock = threading.Lock()

        # Initialize pygame before creating any game objects
        pygame.init()

        # Set display mode with safe defaults
        self.width, self.height = 800, 600
        self.screen = None
        try:
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption("Air Hockey Minimal Client")
        except pygame.error as e:
            print(f"Error setting display mode: {e}")
            sys.exit(1)

        # Basic colors
        self.WHITE = (255, 255, 255)
        self.BLACK = (0, 0, 0)
        self.RED = (255, 0, 0)
        self.BLUE = (0, 0, 255)
        self.GRAY = (100, 100, 100)

        # Create WebSocket connection in a separate thread
        self.ws = None
        threading.Thread(target=self.connect_websocket, daemon=True).start()

        print("Client initialized.")

    def connect_websocket(self):
        """Connect to WebSocket server in a separate thread"""
        try:
            print(f"Connecting to {self.server_url}...")

            # Define WebSocket callbacks
            def on_open(ws):
                print("WebSocket connection opened")
                self.connected = True

            def on_message(ws, message):
                try:
                    print(f"Message received (first 50 chars): {message[:50]}...")
                    # Store message for debugging
                    self.last_message = message

                    # Parse message with thread safety
                    parsed = json.loads(message)
                    with self.state_lock:
                        self.game_state = parsed
                except Exception as e:
                    print(f"Error in on_message: {e}")

            def on_error(ws, error):
                print(f"WebSocket error: {error}")

            def on_close(ws, close_status_code, close_msg):
                print(f"WebSocket closed: {close_status_code} - {close_msg}")
                self.connected = False

            # Create and connect WebSocket
            self.ws = websocket.WebSocketApp(
                self.server_url,
                on_open=on_open,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close
            )

            # Start WebSocket connection (blocking call)
            self.ws.run_forever()

        except Exception as e:
            print(f"WebSocket connection error: {e}")
            self.connected = False

    def send_movement(self, dx, dy):
        """Send movement to server"""
        if not self.connected or not self.ws:
            return

        try:
            message = json.dumps({"dx": dx, "dy": dy})
            self.ws.send(message)
        except Exception as e:
            print(f"Error sending movement: {e}")

    def draw_circle(self, color, position, radius, border=0):
        """Safely draw a circle with error handling"""
        try:
            if self.screen is None:
                return

            # Ensure position and radius are valid integers
            x = int(position[0]) if position and len(position) > 0 else 0
            y = int(position[1]) if position and len(position) > 1 else 0
            r = int(radius) if radius else 10

            # Draw the circle
            pygame.draw.circle(self.screen, color, (x, y), r, border)
        except Exception as e:
            print(f"Error drawing circle: {e}")

    def draw_text(self, text, color, position, size=24):
        """Safely draw text with error handling"""
        try:
            if self.screen is None:
                return

            font = pygame.font.Font(None, size)
            text_surface = font.render(str(text), True, color)
            self.screen.blit(text_surface, position)
        except Exception as e:
            print(f"Error drawing text: {e}")

    def process_events(self):
        """Process pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

    def process_input(self):
        """Process keyboard input"""
        try:
            dx, dy = 0, 0
            keys = pygame.key.get_pressed()

            if keys[pygame.K_LEFT]:
                dx = -1
            if keys[pygame.K_RIGHT]:
                dx = 1
            if keys[pygame.K_UP]:
                dy = -1
            if keys[pygame.K_DOWN]:
                dy = 1

            if dx != 0 or dy != 0:
                self.send_movement(dx, dy)
        except Exception as e:
            print(f"Error processing input: {e}")

    def draw_debug_info(self):
        """Draw debug information on screen"""
        try:
            # Connection status
            status = "Connected" if self.connected else "Disconnected"
            self.draw_text(f"Status: {status}", self.WHITE, (10, self.height - 40))

            # Last message
            if self.last_message:
                msg_preview = self.last_message[:20] + "..." if len(self.last_message) > 20 else self.last_message
                self.draw_text(f"Last msg: {msg_preview}", self.WHITE, (10, self.height - 20))
        except Exception as e:
            print(f"Error drawing debug info: {e}")

    def render(self):
        """Render the game state"""
        try:
            # Start with clear screen
            if self.screen:
                self.screen.fill(self.BLACK)

            # Access game state with thread safety
            game_state = None
            with self.state_lock:
                if self.game_state:
                    # Make a shallow copy to avoid thread issues
                    game_state = dict(self.game_state)

            if not game_state:
                # Show waiting screen
                self.draw_text("Waiting for game data...", self.WHITE, (self.width//2 - 150, self.height//2))
                self.draw_debug_info()
                pygame.display.flip()
                return

            # Draw field
            try:
                # Get screen dimensions from server if available
                if "game_screen_width" in game_state and "game_screen_height" in game_state:
                    server_width = int(game_state["game_screen_width"])
                    server_height = int(game_state["game_screen_height"])

                    # Update screen size if needed
                    if server_width != self.width or server_height != self.height:
                        try:
                            self.width = server_width
                            self.height = server_height
                            self.screen = pygame.display.set_mode((self.width, self.height))
                        except pygame.error as e:
                            print(f"Error resizing screen: {e}")

                # Draw field outline
                pygame.draw.rect(self.screen, self.WHITE, (0, 0, self.width, self.height), 2)

                # Draw center line
                pygame.draw.line(self.screen, self.WHITE,
                                 (0, self.height//2), (self.width, self.height//2), 1)
            except Exception as e:
                print(f"Error drawing field: {e}")

            # Draw players and ball with minimal error checking
            try:
                # Player 1
                if "player1" in game_state:
                    player1 = game_state["player1"]
                    if "position" in player1 and "radius" in player1:
                        color = self.RED  # Default color
                        self.draw_circle(color, player1["position"], player1["radius"])

                        # Draw score
                        if "player_name" in player1 and "score" in player1:
                            score_text = f"{player1['player_name']}: {player1['score']}"
                            self.draw_text(score_text, self.RED, (10, 10))
            except Exception as e:
                print(f"Error drawing player1: {e}")

            try:
                # Player 2
                if "player2" in game_state:
                    player2 = game_state["player2"]
                    if "position" in player2 and "radius" in player2:
                        color = self.BLUE  # Default color
                        self.draw_circle(color, player2["position"], player2["radius"])

                        # Draw score
                        if "player_name" in player2 and "score" in player2:
                            score_text = f"{player2['player_name']}: {player2['score']}"
                            score_width = len(score_text) * 15  # Rough estimate of text width
                            self.draw_text(score_text, self.BLUE, (self.width - score_width - 10, 10))
            except Exception as e:
                print(f"Error drawing player2: {e}")

            try:
                # Ball
                if "ball" in game_state:
                    ball = game_state["ball"]
                    if "position" in ball and "radius" in ball:
                        color = self.WHITE  # Default color
                        self.draw_circle(color, ball["position"], ball["radius"])
            except Exception as e:
                print(f"Error drawing ball: {e}")

            # Draw debug info
            self.draw_debug_info()

            # Update display
            pygame.display.flip()

        except Exception as e:
            print(f"Render error: {e}")

    def run(self):
        """Main game loop"""
        print("Starting game loop...")
        try:
            while self.running:
                # Process events and input
                self.process_events()
                self.process_input()

                # Render game
                self.render()

                # Cap the frame rate
                pygame.time.delay(33)  # ~30 FPS

        except Exception as e:
            print(f"Game loop error: {e}")
        finally:
            # Clean up
            if self.ws:
                self.ws.close()

            pygame.quit()

            # Dump last message for debugging
            if self.last_message:
                print("\nLast received message:")
                print(f"{self.last_message}")

            print("Game terminated.")

# Run the game
if __name__ == "__main__":
    print(f"Starting Air Hockey client. Python version: {sys.version}")
    print(f"PyGame version: {pygame.version.ver}")
    print(f"OS: {os.name}")

    try:
        client = MinimalAirHockeyClient()
        client.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()