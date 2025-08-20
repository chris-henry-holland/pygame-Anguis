# library/src/anguis/__main__.py

from anguis.game import Game

def main() -> None:
    game = Game(
        arena_shape=(15, 16),
        move_rate=15,
        n_fruit=1,
        head_init_direct=(0, 0)
    )
    game.run()

if __name__ == "__main__":
    main()
