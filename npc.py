import pygame


class NPC(pygame.sprite.Sprite):
    def __init__(self, pos, groups, dialogue):
        super().__init__(groups)
        self.z = 1
        self.frames = [
            pygame.image.load(f'graphics/npc{i}.png').convert_alpha()
            for i in range(1, 3)
        ]
        self.frame_index = 0
        self.animation_speed = 0.05
        self.image = self.frames[0]
        self.rect = self.image.get_rect(topleft=pos)
        self.hitbox = self.rect.inflate(0, -2)
        self.dialogue = dialogue

    def animate(self):
        self.frame_index = (self.frame_index + self.animation_speed) % len(self.frames)
        self.image = self.frames[int(self.frame_index)]

    def update(self):
        self.animate()
