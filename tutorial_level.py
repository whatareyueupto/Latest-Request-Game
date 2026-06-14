import pygame
import sys
from default import TILESIZE
from tile import Tile
from player import Player
from item import SwordItem
from level import YSortCameraGroup

TUTORIAL_MAP = [
    ['x','x','x','x','x','x','x','x','x','x','x','x'],
    ['x',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','x'],
    ['x',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','x'],
    ['x',' ','p',' ',' ',' ',' ',' ',' ',' ',' ','x'],
    ['x',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','x'],
    ['x',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','x'],
    ['x',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','x'],
    ['x',' ',' ',' ',' ',' ',' ',' ',' ','w',' ','x'],
    ['x',' ',' ',' ',' ',' ',' ',' ',' ',' ',' ','x'],
    ['x','x','x','x','x','x','x','x','x','x','x','x'],
]


class TutorialLevel:
    def __init__(self, surface, next_scene):
        self.display_surface = surface
        self.next_scene = next_scene
        self.visible_sprites = YSortCameraGroup(surface)
        self.obstacle_sprites = pygame.sprite.Group()
        self.item_sprites = pygame.sprite.Group()
        self._font = pygame.font.Font('graphics/m5x7.ttf', 32)
        self._create_map()

    def _create_map(self):
        for row_i, row in enumerate(TUTORIAL_MAP):
            for col_i, col in enumerate(row):
                x, y = col_i * TILESIZE, row_i * TILESIZE
                if col == 'x':
                    Tile((x, y), [self.visible_sprites, self.obstacle_sprites], 'x')
                elif col == 'p':
                    self.player = Player((x, y), [self.visible_sprites], self.obstacle_sprites)
                    Tile((x, y), [self.visible_sprites], ' ')
                elif col == 'w':
                    SwordItem((x, y), [self.visible_sprites, self.item_sprites])
                    Tile((x, y), [self.visible_sprites], ' ')
                else:
                    Tile((x, y), [self.visible_sprites], ' ')

    def run(self, events=None):
        for event in (events or []):
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        self.visible_sprites.update()
        self.visible_sprites.custom_draw(self.player)
        for item in pygame.sprite.spritecollide(self.player, self.item_sprites, True):
            self.player.inventory.append(item.item_type)
            if item.item_type == 'sword':
                return self.next_scene
        return None

    def draw_ui(self, screen):
        hints = [
            'Use arrow keys to move around',
            'Walk over the sword to pick it up',
        ]
        for i, line in enumerate(hints):
            surf = self._font.render(line, True, (220, 220, 220))
            screen.blit(surf, (16, 16 + i * 40))
