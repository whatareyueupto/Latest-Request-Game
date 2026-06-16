import pygame


class Item(pygame.sprite.Sprite):
    def __init__(self, pos, groups, image_path, item_type):
        super().__init__(groups)
        self.z = 1
        self.item_type = item_type
        self.image = pygame.image.load(image_path).convert_alpha()
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.copy()

    def update(self):
        pass


class KeyItem(Item):
    def __init__(self, pos, groups):
        super().__init__(pos, groups, 'graphics/key1.png', 'key')
        self.frames = [pygame.image.load(f'graphics/key{i}.png').convert_alpha() for i in range(1, 5)]
        self.frame_index = 0.0

    def update(self):
        self.frame_index = (self.frame_index + 0.075) % len(self.frames)
        self.image = self.frames[int(self.frame_index)]


class SwordItem(Item):
    def __init__(self, pos, groups):
        super().__init__(pos, groups, 'graphics/sword.png', 'sword')
