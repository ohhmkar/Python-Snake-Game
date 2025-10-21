import pygame, sys, random,os
from pathlib import Path
from pygame.math import Vector2
pygame.init()

title_font = pygame.font.Font(None, 60)
score_font = pygame.font.Font(None, 40)

TITLE_SCREEN = "TITLE"
PAUSED = "PAUSED"
RUNNING = "RUNNING"
STOPPED = "STOPPED"

SETTINGS = "SETTINGS"



GREEN = (173, 204, 96)
DARK_GREEN = (43, 51, 24)
BLACK = (0, 0, 0)

RESOLUTIONS = {
	"LOW": (600, 600),
	"MEDIUM": (800, 800),
	"HIGH": (1000, 1000)
}

GAME_MODES = {
	"CLASSIC":{
		"description": "Classic Snake Gameplay",
		"color" : DARK_GREEN
	},
	"MAZE":{
		"description": "Navigate through walls",
		"color": (139,69,19) #brown
	},
	"NO WALLS": {
		"description": "Pass through walls freely",
		"color": (65,105,225) #aquamarine
	},
	"SPEEDRUN":{
		"description": "Ramp it up!",
		"color":(220,20,60) #crimson red

	}
}

DIFFICULTY_SPEEDS = {
	"EASY": 200,
	"MEDIUM": 150,
	"HARD": 100,
	"EXTREME": 75
}

POWERUP_TYPES = {
	"DOUBLE_POINTS": {"color": (255, 215, 0), "duration": 5000, "symbol":"2x"},#gold
	"GHOST" : {"color":(200,200,200),"duration":3000,"symbol":"G"}, #silver
	"SLOW_TIME": {"color":(0,191,255),"duration":4000,"symbol":"S"}, #blue
	"SHRINK": {"color":(255,99,71),"duration":2000,"symbol":"small"} #red
}

cell_size = 30
number_of_cells = 25

OFFSET = 75
def load_high_score():
	try:
		with open("high_score.txt", "r") as file:
			return int(file.read())
	except FileNotFoundError:
		return 0
def save_high_score(score):
	with open("high_score.txt", "w") as file:
		file.write(str(score))

class Button:
	def __init__(self, x, y, width, height, text, color):
		self.text = text
		self.color = color
		self.font = pygame.font.Font(None, 40)
		text_surface = self.font.render(text, True, BLACK)
		text_width = text_surface.get_width()
		self.width = max(width, text_width + 20)
		self.height = height

		self.x = x - (self.width - width) // 2
		self.rect = pygame.Rect(self.x, y, self.width, self.height)
		
	def draw(self, surface):
		pygame.draw.rect(surface, self.color, self.rect, border_radius=12)
		text_surface = self.font.render(self.text, True, BLACK)
		text_rect = text_surface.get_rect(center=self.rect.center)
		surface.blit(text_surface, text_rect)

	@property
	def text(self):
		return self._text
	@text.setter
	def text(self, new_text):
		self._text = new_text
		if hasattr(self, 'font'):
			text_surface = self.font.render(new_text, True, BLACK)
			text_width = text_surface.get_width()
			new_width = max(self.rect.width, text_width+40)

			center_x = self.rect.centerx
			self.rect.width = new_width
			self.rect.centerx = center_x
	
	def is_clicked(self, pos):
		return self.rect.collidepoint(pos)

class PowerUp:
	def __init__(self, snake_body):
		self.position = Vector2(-1, -1)
		self.active = False
		self.type = None
		self.surface = pygame.Surface((cell_size, cell_size))
		self.pickup_sound = pygame.mixer.Sound("Sounds/powerup.mp3")
		self.font = pygame.font.Font(None, 30)

	def spawn(self, snake_body):
		if random.random() < 0.25:  # 25% chance
			self.position = self.generate_random_pos(snake_body)
			self.type = random.choice(list(POWERUP_TYPES.keys()))
			self.surface.fill(POWERUP_TYPES[self.type]["color"])
			self.active = True
	
	def generate_random_pos(self,snake_body):
		x = random.randint(0, number_of_cells-1)
		y = random.randint(0, number_of_cells-1)
		pos = Vector2(x, y)
		while pos in snake_body:
			x = random.randint(0, number_of_cells-1)
			y = random.randint(0, number_of_cells-1)
			pos = Vector2(x, y)	
		return pos
	def draw(self):
		if self.active:
			powerup_rect = pygame.Rect(OFFSET + self.position.x * cell_size, OFFSET + self.position.y * cell_size, cell_size, cell_size)
			screen.blit(self.surface, powerup_rect)

			# Ensure self.type is valid before indexing POWERUP_TYPES to avoid type errors
			if self.type is not None and self.type in POWERUP_TYPES:
				symbol_text = POWERUP_TYPES[self.type].get("symbol", "")
				symbol = self.font.render(symbol_text, True, BLACK)
				symbol_rect = symbol.get_rect(center=powerup_rect.center)
				screen.blit(symbol, symbol_rect)
class Food:
	def __init__(self, snake_body):
		self.position = self.generate_random_pos(snake_body)

	def draw(self):
		food_rect = pygame.Rect(OFFSET + self.position.x * cell_size, OFFSET + self.position.y * cell_size, 
			cell_size, cell_size)
		screen.blit(food_surface, food_rect)

	def generate_random_cell(self):
		x = random.randint(0, number_of_cells-1)
		y = random.randint(0, number_of_cells-1)
		return Vector2(x, y)

	def generate_random_pos(self, snake_body):
		position = self.generate_random_cell()
		while position in snake_body:
			position = self.generate_random_cell()
		return position

class Snake:
	def __init__(self):
		self.body = [Vector2(6, 9), Vector2(5,9), Vector2(4,9)]
		self.direction = Vector2(1, 0)
		self.add_segment = False
		self.last_direction = Vector2(1,0)
		self.ghost_mode = False
		self.eat_sound = pygame.mixer.Sound("Sounds/eat.mp3")
		self.wall_hit_sound = pygame.mixer.Sound("Sounds/wall.mp3")


	def draw(self):
		for segment in self.body:
			segment_rect = (OFFSET + segment.x * cell_size, OFFSET+ segment.y * cell_size, cell_size, cell_size)
			pygame.draw.rect(screen, DARK_GREEN, segment_rect, 0, 7)

	def update(self):
		self.body.insert(0, self.body[0] + self.direction)
		self.last_direction = self.direction
		if self.add_segment == True:
			self.add_segment = False
		else:
			self.body = self.body[:-1]
		
	def can_change_direction(self, new_direction):
		#180 turns was killing snake so, added
		return (self.last_direction.x * new_direction.x ==0 and self.last_direction.y * new_direction.y == 0)

	def reset(self):
		self.body = [Vector2(6,9), Vector2(5,9), Vector2(4,9)]
		self.direction = Vector2(1, 0)
	
	def play_eat_sound(self):
		if game.sound_enabled:
			self.eat_sound.play()
	
	def play_wall_hit_sound(self):
		if game.sound_enabled:
			self.wall_hit_sound.play()
		
	def play_powerup_sound(self):
		if game.sound_enabled:
			try:
				pygame.mixer.Sound("Sounds/powerup.mp3").play()
			except Exception:
				pass #to avoid crashes if sound file is missing

	

SNAKE_UPDATE = pygame.USEREVENT
pygame.time.set_timer(SNAKE_UPDATE, 200) 	

class Game:
	def __init__(self):
		
		self.snake = Snake()
		self.food = Food(self.snake.body)
		self.state = "TITLE"
		self.score = 0
		self.difficulty = "MEDIUM"
		self.update_speed()
		self.started = False
		self.high_score = load_high_score()
		self.powerup = PowerUp(self.snake.body)
		self.score_multiplier = 1
		self.powerup_end_time = 0	
		self.powerup_type = None
		screen_center_x = OFFSET + (cell_size * number_of_cells) / 2
		button_width = 200
		button_height = 50
		button_x = screen_center_x - button_width // 2
		self.play_button = Button(screen_center_x - 60,300,120,50, "PLAY", DARK_GREEN)
		self.resume_button = Button(screen_center_x - 60, 300, 120, 50, "RESUME", DARK_GREEN)
		self.game_mode = "CLASSIC"
		self.mode_button = Button(button_x,440,button_width,button_height,f"MODE: {self.game_mode}",DARK_GREEN)
		self.walls = []
		self.current_resolution = RESOLUTIONS["MEDIUM"]
		self.sound_enabled = True
		screen_center_x = OFFSET + (cell_size * number_of_cells) / 2
		

		self.play_button = Button(button_x, 300, button_width, button_height, "PLAY", DARK_GREEN)
		self.settings_button = Button(button_x, 370, button_width, button_height, "SETTINGS", DARK_GREEN)	

		self.resolution_button = Button(button_x, 250, button_width, button_height,f"RESOLUTION: {list(RESOLUTIONS.keys())[0]}", DARK_GREEN)
		self.sound_button = Button(button_x, 320, button_width, button_height, "SOUND: ON", DARK_GREEN)
		self.back_button = Button(button_x, 390, button_width, button_height, "BACK", DARK_GREEN)
		self.resume_button = Button(button_x, 300, button_width, button_height, "RESUME", DARK_GREEN)

	def change_game_mode(self):
		modes = list(GAME_MODES.keys())
		current_index = modes.index(self.game_mode)
		self.game_mode = modes[(current_index + 1) % len(modes)]
		self.mode_button.text = f"MODE: {self.game_mode}"
		self.reset_game_mode()
	def reset_game_mode(self):
		self.walls = []
		if self.game_mode == "MAZE":
			self.generate_maze()
		elif self.game_mode == "SPEED_RUN":
			self.difficulty = "EASY"
			self.update_speed()
	
	def generate_maze(self):
		self.walls = []
		for _ in range(15):
			wall_x = random.randint(0, number_of_cells - 3)
			wall_y = random.randint(0, number_of_cells - 3)
			wall_pos = Vector2(wall_x, wall_y)
			if wall_pos not in self.snake.body and wall_pos != self.food.position:
				self.walls.append(wall_pos)
		
	def draw_maze(self):
		if self.game_mode == "MAZE":
			for wall in self.walls:
				wall_rect = pygame.Rect(OFFSET + wall.x * cell_size, OFFSET + wall.y * cell_size, cell_size, cell_size)
				pygame.draw.rect(screen, GAME_MODES["MAZE"]["color"], wall_rect) #brown walls

	def draw_settings_screen(self):
		screen.fill(GREEN)
		title_text = title_font.render("SETTINGS", True, DARK_GREEN)
		title_rect = title_text.get_rect(center=(OFFSET + (cell_size*number_of_cells)/2, 150))
		screen.blit(title_text, title_rect)

		self.resolution_button.draw(screen)
		self.sound_button.draw(screen)
		self.back_button.draw(screen)

	def toggle_sound(self):
		self.sound_enabled = not self.sound_enabled
		self.sound_button.text = "SOUND: ON" if self.sound_enabled else "SOUND: OFF"

	def change_resolution(self):
		resolutions = list(RESOLUTIONS.keys())
		current_res = next(k for k,v in RESOLUTIONS.items() if v == self.current_resolution)
		current_index = resolutions.index(current_res)
		new_index = (current_index + 1) % len(resolutions)
		new_res = resolutions[new_index]
		self.current_resolution = RESOLUTIONS[new_res]
		self.resolution_button.text = f"RESOLUTION: {new_res}"
		self.apply_resolution()
	
	def apply_resolution(self):
		global screen, cell_size
		width, height = self.current_resolution
		screen = pygame.display.set_mode((width, height))
		cell_size = (width - 2 * OFFSET) // number_of_cells
	def draw_title_screen(self):
		screen.fill(GREEN)
		title_text = title_font.render("RETRO SNAKE", True, DARK_GREEN)
		title_rect = title_text.get_rect(center=(OFFSET + (cell_size*number_of_cells)/2, 200))
		screen.blit(title_text, title_rect)

		self.play_button.draw(screen)
		self.settings_button.draw(screen)
		self.mode_button.draw(screen)

		mode_desc = score_font.render(GAME_MODES[self.game_mode]["description"], True, GAME_MODES[self.game_mode]["color"])
		desc_rect = mode_desc.get_rect(center=(OFFSET + (cell_size*number_of_cells)/2, 510))
		screen.blit(mode_desc, desc_rect)

		self.play_button.draw(screen)
		self.settings_button.draw(screen)
	
	def draw_pause_screen(self):
		overlay = pygame.Surface((screen.get_width(), screen.get_height()))
		overlay.set_alpha(128) 
		overlay.fill((0, 0, 0))
		screen.blit(overlay, (0, 0))
		pause_text = title_font.render("PAUSED", True, DARK_GREEN)
		pause_rect = pause_text.get_rect(center=(OFFSET + (cell_size*number_of_cells)/2, 200))
		screen.blit(pause_text, pause_rect)
		self.resume_button.draw(screen)

	
	def update_high_score(self):
		if self.score > self.high_score:
			self.high_score = self.score
			save_high_score(self.high_score)

	def start_prompt(self):
		if not self.started and self.state == "RUNNING":
			start_text = score_font.render("Press any arrow key to start", True, DARK_GREEN)
			start_rect = start_text.get_rect(center=(OFFSET + (cell_size*number_of_cells)/2, OFFSET + (cell_size*number_of_cells)/2))
			screen.blit(start_text, start_rect)
	def update_speed(self):
		pygame.time.set_timer(SNAKE_UPDATE,DIFFICULTY_SPEEDS[self.difficulty])
	def change_difficulty(self, new_difficulty):
		self.difficulty = new_difficulty
		self.update_speed()
	
	def draw(self):
		self.food.draw()
		self.snake.draw()
		self.powerup.draw()
		if self.game_mode == "MAZE":
			self.draw_maze()

	def update(self):
		if self.state == "RUNNING" and self.started:
			self.snake.update()
			self.check_collision_with_food()
			self.check_collision_with_edges()
			self.check_collision_with_tail()
			self.check_collision_with_powerup()
			self.update_powerup_status()
			if self.game_mode == "SPEEDRUN" and self.score >0:
				base_speed = DIFFICULTY_SPEEDS[self.difficulty]
				speed_decreases = min(self.score * 5 , 100) 
				new_speed = max(75, base_speed - speed_decreases)
				pygame.time.set_timer(SNAKE_UPDATE,new_speed)
			if random.random() < 0.025:
				self.powerup.spawn(self.snake.body)	
	
	def check_collision_with_powerup(self):
		if self.powerup.active and self.snake.body[0] == self.powerup.position:
			self.activate_powerup()
	
	def activate_powerup(self):
		self.powerup.active = False
		if self.powerup.type == "DOUBLE_POINTS":
			self.score_multiplier = 2
		elif self.powerup.type == "GHOST":
			self.snake.ghost_mode = True
		elif self.powerup.type == "SLOW_TIME":
			self.change_difficulty("EASY")
		elif self.powerup.type == "SHRINK":
			if len(self.snake.body) > 3:
				segments_to_remove = min(3,len(self.snake.body) -3)
				self.snake.body = self.snake.body[:-segments_to_remove]
		
		self.powerup_type = self.powerup.type
		self.powerup_end_time = pygame.time.get_ticks() + POWERUP_TYPES[self.powerup.type]["duration"]
		if self.sound_enabled:
			self.powerup.pickup_sound.play()

	def update_powerup_status(self):
		if pygame.time.get_ticks() >= self.powerup_end_time:
			if self.powerup_type == "DOUBLE_POINTS":
				self.score_multiplier = 1
			elif self.powerup_type == "GHOST":
				self.snake.ghost_mode = False
			elif self.powerup_type == "SLOW_TIME":
				self.change_difficulty(self.difficulty)
			self.powerup_type = None
	
	def draw_powerup_status(self):
		if self.powerup_type:
			status_text = ""
			if self.powerup_type == "DOUBLE_POINTS":
				status_text = "2x POINTS ACTIVE!"
				color = POWERUP_TYPES["DOUBLE_POINTS"]["color"]
			elif self.powerup_type == "GHOST":
				status_text = "GHOST MODE ACTIVE!"
				color = POWERUP_TYPES["GHOST"]["color"]
			elif self.powerup_type == "SLOW_TIME":
				status_text = "SLOW TIME ACTIVE!"
				color = POWERUP_TYPES["SLOW_TIME"]["color"]
			elif self.powerup_type == "SHRINK":
				status_text = "SHRINK ACTIVE!"
				color = POWERUP_TYPES["SHRINK"]["color"]
			
			powerup_text = score_font.render(status_text, True, color)
			powerup_rect = powerup_text.get_rect(midtop=(OFFSET + (cell_size*number_of_cells)/2, 20))
			screen.blit(powerup_text, powerup_rect)
			
	def check_collision_with_food(self):
		if self.snake.body[0] == self.food.position:
			self.food.position = self.food.generate_random_pos(self.snake.body)
			self.snake.add_segment = True
			self.score += 1 * self.score_multiplier
			if self.sound_enabled:
				self.snake.eat_sound.play()

	def check_collision_with_edges(self):
		if self.snake.ghost_mode or self.game_mode == "NO WALLS":
			self.snake.body[0].x = self.snake.body[0].x % number_of_cells
			self.snake.body[0].y = self.snake.body[0].y % number_of_cells
			return False
		elif self.game_mode == "MAZE":
			if self.snake.body[0] in self.walls:
				self.game_over()
		if self.snake.body[0].x == number_of_cells or self.snake.body[0].x == -1:
			self.game_over()
		if self.snake.body[0].y == number_of_cells or self.snake.body[0].y == -1:
			self.game_over()

	def game_over(self):
		self.update_high_score()
		self.snake.reset()
		self.food.position = self.food.generate_random_pos(self.snake.body)
		self.state = "STOPPED"
		self.score = 0
		self.score_multiplier = 1
		self.powerup.active = False
		self.started = False
		if self.game_mode == "MAZE":
			self.generate_maze()
		if self.sound_enabled:
			self.snake.wall_hit_sound.play()

	def check_collision_with_tail(self):
		headless_body = self.snake.body[1:]
		if self.snake.body[0] in headless_body:
			self.game_over()
		

screen = pygame.display.set_mode((2*OFFSET + cell_size*number_of_cells, 2*OFFSET + cell_size*number_of_cells))

pygame.display.set_caption("Retro Snake")

clock = pygame.time.Clock()

game = Game()
food_surface = pygame.image.load("Graphics/food.png")



while True:
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			pygame.quit()
			sys.exit()
		
		if event.type == pygame.MOUSEBUTTONDOWN:
			mouse_pos = pygame.mouse.get_pos()
			if game.state == "TITLE":
				if game.play_button.is_clicked(mouse_pos):
					game.state = "RUNNING"
				elif game.settings_button.is_clicked(mouse_pos):
					game.state = "SETTINGS"
				elif game.mode_button.is_clicked(mouse_pos):
					game.change_game_mode()
			elif game.state == "SETTINGS":
				if game.resolution_button.is_clicked(mouse_pos):
					game.change_resolution()
				elif game.sound_button.is_clicked(mouse_pos):
					game.toggle_sound()
				elif game.back_button.is_clicked(mouse_pos):
					game.state = "TITLE"
			elif game.state == "PAUSED" and game.resume_button.is_clicked(mouse_pos):
				game.state = "RUNNING"
				
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_ESCAPE:
				if game.state == "RUNNING":
					game.state = "PAUSED"
				elif game.state == "PAUSED":
					game.state = "RUNNING"
		

		if event.type == pygame.KEYDOWN:
			if game.state == "STOPPED":
				game.state = "RUNNING"
				game.started = False
			if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
				game.started = True
			if event.key == pygame.K_1:
				game.change_difficulty("EASY")
			if event.key == pygame.K_2:
				game.change_difficulty("MEDIUM")
			if event.key == pygame.K_3:
				game.change_difficulty("HARD")
			if event.key == pygame.K_4:
				game.change_difficulty("EXTREME")
			
			if event.key == pygame.K_UP and game.snake.can_change_direction(Vector2(0, -1)):
				game.snake.direction = Vector2(0, -1)
			if event.key == pygame.K_DOWN and game.snake.can_change_direction((Vector2(0,1))):
				game.snake.direction = Vector2(0, 1)
			if event.key == pygame.K_LEFT and game.snake.can_change_direction(Vector2(-1, 0)):
				game.snake.direction = Vector2(-1, 0)
			if event.key == pygame.K_RIGHT and game.snake.can_change_direction(Vector2(1, 0)):
				game.snake.direction = Vector2(1, 0)
			
		if event.type == SNAKE_UPDATE and game.state == "RUNNING":
			game.update()

	if game.state == "TITLE":
		game.draw_title_screen()
	elif game.state == "SETTINGS":
		game.draw_settings_screen()
	elif game.state == "PAUSED":
		game.draw_pause_screen()
	else:	
		screen.fill(GREEN)
		pygame.draw.rect(screen, DARK_GREEN, 
			(OFFSET-5, OFFSET-5, cell_size*number_of_cells+10, cell_size*number_of_cells+10), 5)
		game.draw()
		
		title_surface = title_font.render("Snake", True, BLACK)
		score_surface = score_font.render(str(game.score), True, DARK_GREEN)
		difficulty_surface = score_font.render("Difficulty: " + game.difficulty, True, DARK_GREEN)
		screen.blit(difficulty_surface, (OFFSET + 200, OFFSET + cell_size*number_of_cells +10))
		difficulty_info = score_font.render("Press 1-4 to change difficulty", True, DARK_GREEN)
		difficulty_info_rect = difficulty_info.get_rect(centerx=OFFSET + (cell_size*number_of_cells)/2,y=OFFSET + cell_size*number_of_cells + 40)
		screen.blit(difficulty_info, difficulty_info_rect)
		screen.blit(score_surface, (OFFSET-5, OFFSET + cell_size*number_of_cells +10))
		high_score_surface = score_font.render("High Score: " + str(game.high_score), True, DARK_GREEN)
		screen.blit(title_surface, (OFFSET-5, 20))
		high_score_rect = high_score_surface.get_rect(topright=(OFFSET + cell_size*number_of_cells - 5, 20))
		screen.blit(high_score_surface, high_score_rect)
		if not game.started:
			game.start_prompt()
		game.draw_powerup_status()
	pygame.display.update()
	clock.tick(60)

