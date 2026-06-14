import pygame,sys
from level import Level
from tutorial_level import TutorialLevel
from default import *
from ble_controller import BleController
from connection_screen import ConnectionScreen


class SceneManager:
    def __init__(self, surface, ble_controller):
        self.ble_controller = ble_controller
        self._was_connected = False
        level = Level(surface, ble_controller)
        tutorial = TutorialLevel(surface, next_scene=level)
        self._scene = ConnectionScreen(ble_controller, next_scene=tutorial)

    def run(self, events):
        connected = self.ble_controller.is_connected()
        if self._was_connected and not connected and not isinstance(self._scene, ConnectionScreen):
            self._scene = ConnectionScreen(self.ble_controller, next_scene=self._scene)
        self._was_connected = connected

        next_scene = self._scene.run(events)
        if next_scene:
            self._scene = next_scene

    def draw_ui(self, screen):
        if hasattr(self._scene, 'draw_ui'):
            self._scene.draw_ui(screen)


class App:
    def __init__(self):
        pygame.init()
        self._running = True
        self.size = WIDTH, HEIGHT
        self.screen = pygame.display.set_mode(self.size)
        pygame.display.set_caption('ReQuest')
        self._game_surf = pygame.Surface((WIDTH // SCALE, HEIGHT // SCALE))
        self.ble_controller = BleController()
        self.scene_manager = SceneManager(self._game_surf, self.ble_controller)

    def run(self):
        while self._running:
            events = pygame.event.get()
            for event in events:
                self.on_event(event)

            self._game_surf.fill('black')
            self.scene_manager.run(events)
            scaled = pygame.transform.scale(self._game_surf, (WIDTH, HEIGHT))
            self.screen.blit(scaled, (0, 0))
            self.scene_manager.draw_ui(self.screen)
            pygame.display.update()

        pygame.quit()
        sys.exit()

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False


if __name__ == "__main__":
    theApp = App()
    theApp.run()