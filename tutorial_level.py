import pygame
import sys
from default import TILESIZE, TUTORIAL_MAP
from tile import Tile
from player import Player
from item import SwordItem
from npc import NPC
from level import YSortCameraGroup

class TutorialLevel:
    def __init__(self, surface, next_scene):
        self.display_surface = surface
        self.next_scene = next_scene
        self.visible_sprites = YSortCameraGroup(surface)
        self.obstacle_sprites = pygame.sprite.Group()
        self.item_sprites = pygame.sprite.Group()
        self.npc_sprites = pygame.sprite.Group()
        self._active_npc = None
        self._npc_talked = False
        self._sword_pos = None
        self._intro_dismissed = False
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
                    right_frames = [pygame.image.load(f'graphics/player-swordless{i}.png').convert_alpha() for i in range(1, 3)]
                    left_frames = [pygame.transform.flip(f, True, False) for f in right_frames]
                    self.player.animations = {'right': right_frames, 'left': left_frames}
                    self.player.image = right_frames[0]
                    Tile((x, y), [self.visible_sprites], ' ')
                elif col == 'w':
                    self._sword_pos = (x, y)
                    Tile((x, y), [self.visible_sprites], ' ')
                elif col == 'n':
                    NPC((x, y), [self.visible_sprites, self.npc_sprites, self.obstacle_sprites],
                        dialogue=["Your strength is undeniable, get ready to battle.",
                                  "A sword lies in this room awaiting you.",
                                  "You can pick up items by walking into it them."])
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

        TALK_RANGE = TILESIZE * 2
        self._active_npc = None
        for npc in self.npc_sprites:
            dx = abs(self.player.rect.centerx - npc.rect.centerx)
            dy = abs(self.player.rect.centery - npc.rect.centery)
            if dx < TALK_RANGE and dy < TALK_RANGE:
                self._active_npc = npc
                break

        if not self._intro_dismissed:
            keys = pygame.key.get_pressed()
            if any(keys[k] for k in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)):
                self._intro_dismissed = True

        if self._active_npc and not self._npc_talked:
            self._npc_talked = True
            if self._sword_pos:
                SwordItem(self._sword_pos, [self.visible_sprites, self.item_sprites])

        for item in pygame.sprite.spritecollide(self.player, self.item_sprites, True):
            self.player.inventory.append(item.item_type)
            if item.item_type == 'sword':
                return self.next_scene
        return None

    def draw_ui(self, screen):
        title = self._font.render('Game Tutorial', True, (220, 220, 220))
        screen.blit(title, (16, 16))

        if not self._intro_dismissed:
            intro_lines = [
                'Use arrow keys to explore the dungeon',
                'Press Q to quit at anytime',
            ]
            pad = 12
            box_h = pad + len(intro_lines) * 36 + pad
            box_rect = pygame.Rect(16, screen.get_height() - box_h - 16,
                                   screen.get_width() - 32, box_h)
            panel = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
            panel.fill((10, 10, 30, 200))
            screen.blit(panel, box_rect.topleft)
            ty = box_rect.top + pad
            for line in intro_lines:
                surf = self._font.render(line, True, (220, 220, 200))
                screen.blit(surf, (box_rect.left + pad, ty))
                ty += surf.get_height() + 4

        if self._active_npc:
            npc = self._active_npc
            pad = 12
            box_h = pad + len(npc.dialogue) * 36 + pad
            box_rect = pygame.Rect(16, screen.get_height() - box_h - 16,
                                   screen.get_width() - 32, box_h)
            panel = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
            panel.fill((10, 10, 30, 200))
            screen.blit(panel, box_rect.topleft)
            ty = box_rect.top + pad
            for line in npc.dialogue:
                surf = self._font.render(line, True, (220, 220, 200))
                screen.blit(surf, (box_rect.left + pad, ty))
                ty += surf.get_height() + 4
