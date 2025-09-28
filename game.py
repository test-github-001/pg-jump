import sys
import pygame as PG

PG.init()

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN = PG.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
PG.display.set_caption("Платформер")

FPS = 60
CLOCK = PG.time.Clock()

PLATFORM_HEIGHT = 20
PLATFORM_WIDTH_STEP = 40
PLATFORM_COLOR = (0, 255, 0)
FINISH_COLOR = (255, 255, 0)

PLAYER_SIZE = 40
PLAYER_SPEED = 5
PLAYER_COLOR = (255, 0, 0)
JUMP_FORCE = -12
GRAVITY = 0.5

level = [
    #                         111111111111111  
    #   1122233444556667788899000112223344455
    #0482604826048260482604826048260482604826
    '                                        ',
    '                                        ',
    '                                        ',
    '                                        ',
    '                                        ',
    '                                        ',
    '                                        ',
    '                                        ',
    '                                        ',
    '                                        ',
    '                                        ',
    '                                        ',
    '                                        ',
    '                                        ',
    '                                        ',
    '                                        ',
    '                   [F]                  ',
    '[x]     [x]    [x]    [x]    [x]     [x]',
    '[xxxxxxxxxxxxxxxxxxPxxxxxxxxxxxxxxxxxxx]',
]

platforms = []
player = None
finish = None

step_x = PLATFORM_WIDTH_STEP
step_y = 80  # Расстояние между строками

LEVEL_WIDTH = len(level[0]) * step_x
LEVEL_HEIGHT = len(level) * step_y

class Player:
    def __init__(self, x, y):
        self.rect = PG.Rect(x, y, PLAYER_SIZE, PLAYER_SIZE)
        self.speed_y = 0
        self.speed_x = 0
        self.is_on_ground = False
        
    def update(self, platforms, keys, is_player_jump):
        if is_player_jump : self.jump()

        self.speed_x = 0
        if keys[PG.K_LEFT] or keys[PG.K_a]:
            self.speed_x = -PLAYER_SPEED
        if keys[PG.K_RIGHT] or keys[PG.K_d]:
            self.speed_x = PLAYER_SPEED

        self.speed_y += GRAVITY
        self.rect.x += self.speed_x
        
        # Горизонтальные коллизии
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.speed_x > 0:
                    self.rect.right = platform.rect.left
                elif self.speed_x < 0:
                    self.rect.left = platform.rect.right
        
        self.rect.y += self.speed_y
        self.is_on_ground = False
        
        # Вертикальные коллизии
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.speed_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.is_on_ground = True
                    self.speed_y = 0
                    if platform.is_finish : return True
                elif self.speed_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.speed_y = 0
        
        # Ограничение в пределах уровня
        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(LEVEL_WIDTH, self.rect.right)
        self.rect.bottom = min(LEVEL_HEIGHT, self.rect.bottom)

        return False
        
    def jump(self):
        if self.is_on_ground:
            self.speed_y = JUMP_FORCE
            
    def draw(self, camera):
        draw_rect = PG.Rect(
            self.rect.x - camera.x, 
            self.rect.y - camera.y, 
            self.rect.width, 
            self.rect.height
        )
        PG.draw.rect(SCREEN, PLAYER_COLOR, draw_rect)

class Platform:
    def __init__(self, x, y, width_range, is_finish=False):
        self.rect = PG.Rect(x, y, width_range * PLATFORM_WIDTH_STEP, PLATFORM_HEIGHT)
        self.is_finish = is_finish
        
    def draw(self, camera):
        draw_rect = PG.Rect(
            self.rect.x - camera.x, 
            self.rect.y - camera.y, 
            self.rect.width, 
            self.rect.height
        )
        color = FINISH_COLOR if self.is_finish else PLATFORM_COLOR
        PG.draw.rect(SCREEN, color, draw_rect)

class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0
        
    def update(self, target):
        self.x = target.rect.centerx - SCREEN_WIDTH // 2
        self.y = target.rect.centery - SCREEN_HEIGHT // 2
        
        self.x = max(0, min(self.x, LEVEL_WIDTH - SCREEN_WIDTH))
        self.y = max(0, min(self.y, LEVEL_HEIGHT - SCREEN_HEIGHT))

def generate_level():
    platforms_list = []
    player_obj = None
    finish_platform = None
    
    y = 0
    for line in level:
        platform_x = 0
        platform_size = 0
        x = 0
        
        for char in line:
            if platform_size > 0: 
                platform_size += 1
                
            if char == '[':
                platform_x = x
                platform_size = 1
            elif char == ']':
                if platform_size > 0:
                    platform = Platform(platform_x, y, platform_size)
                    platforms_list.append(platform)
                    platform_size = 0
            elif char == 'P':
                # Создаем игрока в этой позиции
                player_obj = Player(x, y - PLAYER_SIZE)
            elif char == 'F':
                # Создаем финишную платформу
                if platform_size > 0:
                    finish_platform = Platform(platform_x, y, platform_size, is_finish=True)
                    platforms_list.append(finish_platform)
                    platform_size = 0
            
            x += step_x
        
        y += step_y
    
    return platforms_list, player_obj, finish_platform

def show_win_message():
    font = PG.font.Font(None, 74)
    text = font.render("ПОБЕДА!", True, (255, 255, 0))
    text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    SCREEN.blit(text, text_rect)

# Инициализация
platforms, player, finish = generate_level()
camera = Camera()

if player is None:
    # Если игрок не указан в уровне, создаем его в центре
    player = Player(LEVEL_WIDTH // 2, LEVEL_HEIGHT // 2)

is_on_loop = True
is_game_won = False

while is_on_loop:
    CLOCK.tick(FPS)

    is_player_jump = False
    
    for event in PG.event.get():
        if event.type == PG.QUIT: 
            is_on_loop = False
        if event.type == PG.KEYDOWN and event.key == PG.K_ESCAPE: 
            is_on_loop = False

        if event.type == PG.KEYDOWN and event.key == PG.K_SPACE:
            is_player_jump = True
    
    if not is_game_won:
        keys = PG.key.get_pressed()
        is_game_won = player.update(platforms, keys, is_player_jump)
        camera.update(player)
    
    # Отрисовка
    SCREEN.fill((0, 0, 0))
    
    for p in platforms: 
        p.draw(camera)
    player.draw(camera)
    
    if is_game_won : show_win_message()
    
    PG.display.flip()

PG.quit()
sys.exit()
