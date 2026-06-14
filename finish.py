import pygame
import sys


class FinishScreen:
    def __init__(self, surface):
        self.display_surface = surface
        self.font_big   = pygame.font.Font('graphics/m5x7.ttf', 64)
        self.font_small = pygame.font.Font('graphics/m5x7.ttf', 32)

    def run(self, events=None):
        self.display_surface.fill((10, 30, 10))
        for event in (events or []):
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                pygame.quit()
                sys.exit()
        return None

    def draw_ui(self, screen):
        w, h = screen.get_size()
        title = self.font_big.render('Well Done! You have completed today\'s exercises', True, (100, 255, 100))
        hint  = self.font_small.render('Press any key to exit', True, (180, 180, 180))
        screen.blit(title, title.get_rect(center=(w // 2, h // 2 - 30)))
        screen.blit(hint,  hint.get_rect(center=(w // 2, h // 2 + 30)))
