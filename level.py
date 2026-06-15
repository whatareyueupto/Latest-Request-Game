import pygame
import random
from default import *
from tile import Tile
from player import Player
from enemy import Enemy
from battle import BattleScreen
from calibration import CalibrationScreen
from finish import FinishScreen
from item import KeyItem


class Level:
    def __init__(self, surface, ble_controller=None):
        self.display_surface = surface
        self.ble_controller = ble_controller

        self.visible_sprites = YSortCameraGroup(surface)
        self.obstacle_sprites = pygame.sprite.Group()
        self.enemy_sprites = pygame.sprite.Group()

        self._last_safe_pos = None
        self.key_sprites = pygame.sprite.Group()
        self._intro_timer = 600
        self._hud_font = pygame.font.Font('graphics/m5x7.ttf', 32)
        self.create_map()

    def create_map(self):
        floor_positions = []
        enemy_types = []
        player_pos = None

        for row_index, row in enumerate(WORLD_MAP):
            for col_index, col in enumerate(row):
                x = col_index * TILESIZE
                y = row_index * TILESIZE
                if col == 'x':
                    Tile((x, y), [self.visible_sprites, self.obstacle_sprites], col)
                elif col == 'p':
                    player_pos = (x, y)
                    self.player = Player((x, y), [self.visible_sprites], self.obstacle_sprites)
                    Tile((x, y), [self.visible_sprites], ' ')
                    floor_positions.append((x, y))
                elif col in ENEMY_MAP:
                    enemy_types.append(ENEMY_MAP[col])
                    floor_positions.append((x, y))
                    Tile((x, y), [self.visible_sprites], ' ')
                elif col == ' ':
                    floor_positions.append((x, y))
                    Tile((x, y), [self.visible_sprites], col)

        # pick random spawn positions, keeping enemies away from player start
        MIN_DIST = TILESIZE * 5
        candidates = [
            pos for pos in floor_positions
            if player_pos is None or (
                abs(pos[0] - player_pos[0]) + abs(pos[1] - player_pos[1]) >= MIN_DIST
            )
        ]
        random.shuffle(candidates)
        for i, enemy_type in enumerate(enemy_types):
            pos = candidates[i % len(candidates)]
            Enemy(pos, [self.visible_sprites, self.enemy_sprites], self.obstacle_sprites, enemy_type)

    def _check_battle(self):
        hits = pygame.sprite.spritecollide(self.player, self.enemy_sprites, False)
        if hits:
            if self.ble_controller and self.ble_controller.is_connected():
                return CalibrationScreen(
                    self.player, hits[0], self.ble_controller,
                    back_to=self, surface=self.display_surface,
                )
            return BattleScreen(self.player, hits[0], back_to=self, surface=self.display_surface)
        return None

    def drop_key(self, pos):
        KeyItem(pos, [self.visible_sprites, self.key_sprites])

    def restore_player_pos(self):
        if self._last_safe_pos:
            self.player.hitbox.topleft = self._last_safe_pos
            self.player.rect.center = self.player.hitbox.center

    def run(self, events=None):
        if self._intro_timer > 0:
            self._intro_timer -= 1
        self._last_safe_pos = self.player.hitbox.topleft
        self.visible_sprites.update()
        self.visible_sprites.custom_draw(self.player)
        for item in pygame.sprite.spritecollide(self.player, self.key_sprites, True):
            self.player.inventory.append(item.item_type)
            if item.item_type == 'key':
                return FinishScreen(self.display_surface)
        battle = self._check_battle()
        if battle:
            self.restore_player_pos()
            return battle
        return None

    def draw_ui(self, screen):
        p = self.player
        text = self._hud_font.render(f'Lv.{p.level}   {p.xp} / {p.xp_to_next()} XP', True, (220, 220, 220))
        screen.blit(text, (12, 12))

        if self._intro_timer > 0:
            intro_lines = ['Defeat all the enemies in this room',
                           'and find the key to complete this level.']
            pad = 12
            box_h = pad + len(intro_lines) * 36 + pad
            box_rect = pygame.Rect(16, screen.get_height() - box_h - 16,
                                   screen.get_width() - 32, box_h)
            panel = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
            panel.fill((10, 10, 30, 200))
            screen.blit(panel, box_rect.topleft)
            ty = box_rect.top + pad
            for line in intro_lines:
                surf = self._hud_font.render(line, True, (220, 220, 200))
                screen.blit(surf, (box_rect.left + pad, ty))
                ty += surf.get_height() + 4


class YSortCameraGroup(pygame.sprite.Group):
	def __init__(self, surface):

		# general setup
		super().__init__()
		self.display_surface = surface
		self.half_width = self.display_surface.get_size()[0] // 2
		self.half_height = self.display_surface.get_size()[1] // 2
		self.offset = pygame.math.Vector2()

	def custom_draw(self,player):
		self.offset.x = player.rect.centerx - self.half_width
		self.offset.y = player.rect.centery - self.half_height

		for sprite in sorted(self.sprites(), key=lambda sprite: (sprite.z, sprite.rect.centery)):
			offset_pos = sprite.rect.topleft - self.offset
			self.display_surface.blit(sprite.image,offset_pos)
