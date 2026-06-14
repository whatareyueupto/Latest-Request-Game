import pygame
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
        self.create_map()

    def create_map(self):
        for row_index, row in enumerate(WORLD_MAP):
            for col_index, col in enumerate(row):
                x = col_index * TILESIZE
                y = row_index * TILESIZE
                if col == 'x':
                    Tile((x, y), [self.visible_sprites, self.obstacle_sprites],col)
                elif col == 'p':
                    self.player = Player((x, y), [self.visible_sprites], self.obstacle_sprites)
                    Tile((x,y), [self.visible_sprites], ' ')
                elif col in ENEMY_MAP:
                    Enemy((x, y), [self.visible_sprites, self.enemy_sprites], self.obstacle_sprites, ENEMY_MAP[col])
                    Tile((x,y), [self.visible_sprites], ' ')
                elif col == ' ':
                    Tile((x,y), [self.visible_sprites], col)

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
        if not hasattr(self, '_hud_font'):
            self._hud_font = pygame.font.Font('graphics/m5x7.ttf', 32)
        p = self.player
        text = self._hud_font.render(f'Lv.{p.level}   {p.xp} / {p.xp_to_next()} XP', True, (220, 220, 220))
        screen.blit(text, (12, 12))


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
