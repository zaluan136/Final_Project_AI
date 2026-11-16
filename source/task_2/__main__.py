import multiprocessing

import pygame

from .play import run


def main() -> None:
    try:
        run()
    finally:
        pygame.quit()


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
