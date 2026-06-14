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
