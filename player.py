import pygame
import json
import os
from default import *
from entity import Entity

SAVE_FILE = 'save.json'


class Player(Entity):
    def __init__(self, pos, groups, obstacle_sprites):
        super().__init__(groups)
        self.obstacle_sprites = obstacle_sprites
        self.speed = 1
        self.status = 'down'
        self.horizontal = 'right'
        self.frame_index = 0
        self.animation_speed = 0.07

        right_frames = [pygame.image.load(f'graphics/player-right{i}.png').convert_alpha() for i in range(1, 5)]
        left_frames = [pygame.transform.flip(f, True, False) for f in right_frames]
        self.animations = {'right': right_frames, 'left': left_frames}

        self.image = self.animations['right'][0]
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(0, -2)
        self.inventory = []
        self._load_save()

    def _load_save(self):
        if os.path.exists(SAVE_FILE):
            data = json.loads(open(SAVE_FILE).read())
            self.xp    = data.get('xp', 0)
            self.level = data.get('level', 1)
        else:
            self.xp    = 0
            self.level = 1

    def _save(self):
        open(SAVE_FILE, 'w').write(json.dumps({'xp': self.xp, 'level': self.level}))

    def xp_to_next(self):
        return self.level * 100

    def add_xp(self, amount):
        self.xp += amount
        levelled_up = False
        while self.xp >= self.xp_to_next():
            self.xp -= self.xp_to_next()
            self.level += 1
            levelled_up = True
        self._save()
        return levelled_up

    def input(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_UP]:
            self.direction.y = -1
            self.status = 'up'
        elif keys[pygame.K_DOWN]:
            self.direction.y = 1
            self.status = 'down'
        else:
            self.direction.y = 0

        if keys[pygame.K_RIGHT]:
            self.direction.x = 1
            self.status = 'right'
            self.horizontal = 'right'
        elif keys[pygame.K_LEFT]:
            self.direction.x = -1
            self.status = 'left'
            self.horizontal = 'left'
        else:
            self.direction.x = 0

    def animate(self):
        anim_key = self.status if self.status in self.animations else self.horizontal
        if self.direction.magnitude() != 0:
            self.frame_index = (self.frame_index + self.animation_speed) % len(self.animations[anim_key])
            self.image = self.animations[anim_key][int(self.frame_index)]
        else:
            self.frame_index = 0
            self.image = self.animations[anim_key][0]

    def update(self):
        self.input()
        self.move()
        self.animate()
