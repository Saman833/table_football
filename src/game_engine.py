def multiply_elements(*args):
    if len(args) == 2:
        if isinstance(args[0], list) and isinstance(args[1], list):
            list1, list2 = args
            if len(list1) != len(list2):
                raise ValueError("Both lists must have the same length.")
            return [a * b for a, b in zip(list1, list2)]
        elif isinstance(args[0], list) and isinstance(args[1], (int, float)):
            return [x * args[1] for x in args[0]]
        elif isinstance(args[1], list) and isinstance(args[0], (int, float)):
            return [x * args[0] for x in args[1]]

        else:
            raise TypeError("Arguments must be either two lists or one list and one number.")
    else:
        raise ValueError("Exactly two arguments are required.")


class Player:
    def __init__(self, color, x_coordinate, y_coordinate, score, radius=15, name="computer", speed=[1, 1]):
        self.x = x_coordinate
        self.y = y_coordinate
        self.score = score
        self.name = name
        self.x_speed = speed[0]
        self.y_speed = speed[1]
        self.color = color
        self.radius = radius
        self.left_x = None 
        self.right_x = None
        self.top_y = None
        self.bottom_y = None

    def move(self, direction):
        self.x, self.y = self.x + direction[0] * self.x_speed, self.y + direction[1] * self.y_speed
        self.x -=  direction[0] * self.x_speed * (self.x + self.radius > self.right_x - 10 or self.x - self.radius < self.left_x)
        self.y -= direction[1] * self.y_speed * (self.y + self.radius > self.bottom_y - 10 or self.y - self.radius < self.top_y)
    def get_info(self):
        return {
            "player_name": self.name,
            "score": self.score,
            "color": self.color,
            "radius": self.radius,
            "position": [self.x, self.y],
            "speed": [self.x_speed, self.y_speed]
        }
    def  update_boundries(self, left_x, right_x, top_y, bottom_y):
        self.left_x = left_x
        self.right_x = right_x
        self.top_y = top_y
        self.bottom_y = bottom_y


class Ball:
    def __init__(self, x_coordinate, y_coordinate, speed: list, radius, direction=[1, 1], color="white"):
        self.x = x_coordinate
        self.y = y_coordinate
        self.speed = speed
        self.radius = radius
        self.color = color
        self.direction = direction
        self.initial_speed = [7, 7]

    def update_speed_time(self):
        self.speed[0] *= .99
        self.speed[1] *= .99
   
    def check_accident_with_wall(self, left_x, right_x, top_y, bottom_y):
        if self.x + self.radius > right_x - 10 or self.x - self.radius < left_x:
            self.direction[0] *= -1
            
        if self.y + self.radius > bottom_y - 10 or self.y - self.radius < top_y:
            self.direction[1] *= -1

    def check_accident_with_player(self, player: Player):
        distance = ((self.x - player.x) ** 2 + (self.y - player.y) ** 2) ** 0.5
        if abs(distance - player.radius - self.radius) < 7:
            self.direction[0] *= -1
            self.direction[1] *= -1
            self.speed = self.initial_speed.copy()

    def check_if_goal(self):
        pass

    def move(self):
        self.x, self.y = self.x + self.speed[0] * self.direction[0], self.y + self.speed[1] * self.direction[1]

    def get_info(self):
        return {
            "position": [self.x, self.y],
            "speed": self.speed,
            "radius": self.radius,
            "color": self.color
        }


class Game:
    def __init__(self, player1: Player, player2: Player):
        self.screen_width = 800
        self.screen_height = 600
        self.player1 = player1
        self.player2 = player2
        self.player1.update_boundries(0, self.screen_width, 0, self.screen_height)
        self.player2.update_boundries(0, self.screen_width, 0, self.screen_height)
        self.ball = Ball(self.screen_width // 2, self.screen_height // 2, [0, 0], 10)
        self.ball_speed = [1, -1]

    def players_update(self, move_info):
        self.player1.move(move_info["player1"])
        self.player2.move(move_info["player2"])

    def ball_updates(self):
        self.ball.update_speed_time()
        self.ball.check_accident_with_player(self.player1)
        self.ball.check_accident_with_player(self.player2)
        self.ball.check_accident_with_wall(0, self.screen_width, 0, self.screen_height)
        self.ball.move()

    def game_step(self, move_info):
        self.players_update(move_info)
        self.ball_updates()
        return self.get_updates()

    def get_updates(self):
        return {
            "player1": self.player1.get_info(),
            "player2": self.player2.get_info(),
            "ball": self.ball.get_info(),
            "game_screen_width": self.screen_width,
            "game_screen_height": self.screen_height,
        }