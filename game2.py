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
JUMP_FORCE = -15
GRAVITY = 0.5

level = [
    #                         111111111111111  
    #   1122233444556667788899000112223344455
    # 482604826048260482604826048260482604826
    #0000000000000000000000000000000000000000
    '                                        ',
    '                                        ',
    '                                        ',
    '[=]                [===F===]            ',
    '        [=]    [=]           [=]     [=]',
    '[=]                [=======]            ',
    '        [=]    [=]           [=]     [=]',
    '[=]                [=======]            ',
    '        [=]    [=]           [=]     [=]',
    '[=]                [=======]            ',
    '        [=]    [=]           [=]     [=]',
    '[==P===================================]',
]

platforms = []
player = None

step_x = PLATFORM_WIDTH_STEP
step_y = 80  # Расстояние между строками

LEVEL_WIDTH = len(level[0]) * step_x
LEVEL_HEIGHT = len(level) * step_y

class Background:
    def __init__(self, image, parallax_scale = 1.5):
        bg = PG.image.load(image).convert()
        min_width = int(LEVEL_WIDTH * 1.5)
        min_height = int(LEVEL_HEIGHT * 1.5)
        image_width, image_height = bg.get_size()
        
        scale_x = min_width / image_width
        scale_y = min_height / image_height
        scale = max(scale_x, scale_y)
        
        self.width = int(image_width * scale)
        self.height = int(image_height * scale)
        self.image = PG.transform.scale(bg, (self.width, self.height))
        self.parallax = 1.0 / parallax_scale
    
    def draw(self, camera):
        level_center_x = LEVEL_WIDTH / 2
        level_center_y = LEVEL_HEIGHT / 2
        
        bg_center_x = self.width / 2
        bg_center_y = self.height / 2
        
        bg_x = (camera.x - level_center_x) * self.parallax + bg_center_x - SCREEN_WIDTH / 2
        bg_y = (camera.y - level_center_y) * self.parallax + bg_center_y - SCREEN_HEIGHT / 2
        
        bg_x = max(0, min(bg_x, self.width - SCREEN_WIDTH))
        bg_y = max(0, min(bg_y, self.height - SCREEN_HEIGHT))
        
        SCREEN.blit(self.image, (0, 0), (bg_x, bg_y, SCREEN_WIDTH, SCREEN_HEIGHT))

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
            sfx_jump.play()
            
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
    is_finish = False
    
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
                    platform = Platform(platform_x, y, platform_size, is_finish)
                    platforms_list.append(platform)
                    platform_size = 0
                    is_finish = False
            elif char == 'P':
                # Создаем игрока в этой позиции
                player_obj = Player(x, y - PLAYER_SIZE)
            elif char == 'F' : is_finish = True
            
            x += step_x
        
        y += step_y
    
    return platforms_list, player_obj

def show_win_message():
    font = PG.font.Font(None, 74)
    text = font.render("ПОБЕДА!", True, (255, 255, 0))
    text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    SCREEN.blit(text, text_rect)

# фон
BG = Background('bg.png')

# фоновая музыка и звуки
PG.mixer.music.load('bgm_1.mp3') # дожидаемся загрузки файла фоновой музыки
PG.mixer.music.set_volume(0.7) # задаем громкость фоновой музыки (0...1)
PG.mixer.music.play(-1)

sfx_jump = PG.mixer.Sound('sfx_bonus.mp3')

# Инициализация
platforms, player = generate_level()
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
    BG.draw(camera)
    
    for p in platforms: 
        p.draw(camera)
    player.draw(camera)
    
    if is_game_won : show_win_message()
    
    PG.display.flip()

PG.quit()
sys.exit()
