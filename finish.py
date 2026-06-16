import pygame
import sys
import request_bridge


class FinishScreen:
    def __init__(self, surface):
        self.display_surface = surface
        self.font_big   = pygame.font.Font('graphics/m5x7.ttf', 64)
        self.font_small = pygame.font.Font('graphics/m5x7.ttf', 32)
        self.key_frames = []
        for i in range(1, 5):
            raw = pygame.image.load(f'graphics/key{i}.png').convert_alpha()
            self.key_frames.append(pygame.transform.scale(
                raw, (raw.get_width() * 8, raw.get_height() * 8)))
        self._key_anim = 0.0

    def run(self, events=None):
        self.display_surface.fill((10, 30, 10))
        self._key_anim = (self._key_anim + 0.075) % len(self.key_frames)
        for event in (events or []):
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                request_bridge.finish_workout()   # space -> dashboard goes to the check-in
                pygame.quit()
                sys.exit()
        return None

    def draw_ui(self, screen):
        w, h = screen.get_size()
        title = self.font_big.render('Well Done! You have completed today\'s exercises', False, (100, 255, 100))
        hint  = self.font_small.render('Press any key to exit', False, (180, 180, 180))
        key_img = self.key_frames[int(self._key_anim)]
        screen.blit(key_img, key_img.get_rect(center=(w // 2, h // 2 - 90)))
        screen.blit(title, title.get_rect(center=(w // 2, h // 2 - 20)))
        dash_hint = self.font_small.render('Log on to dashboard to submit your session check-in', False, (160, 220, 160))
        screen.blit(dash_hint, dash_hint.get_rect(center=(w // 2, h // 2 + 30)))
        screen.blit(hint, hint.get_rect(center=(w // 2, h // 2 + 70)))
