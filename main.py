import pygame
from src.constants import SCREEN_W, SCREEN_H
from src.game import Game


def main():
    # Boots pygame/audio, opens the window, and hands control to the Game loop
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("py-pong by aryan")
    game = Game(screen)
    game.run()
    pygame.quit()


if __name__ == "__main__":
    main()
