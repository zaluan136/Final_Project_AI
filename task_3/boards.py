from .model import Board, Cell

BLOCK = Cell("block")
WHITE = Cell("cell")


DEMO = Board(
    "Demo 5×5",
    [
        [BLOCK, BLOCK, Cell("clue", down=21), Cell("clue", down=14), BLOCK],
        [BLOCK, Cell("clue", down=14, across=12), WHITE, WHITE, Cell("clue", down=11)],
        [Cell("clue", across=21), WHITE, WHITE, WHITE, WHITE],
        [Cell("clue", across=11), WHITE, WHITE, WHITE, WHITE],
        [BLOCK, Cell("clue", across=16), WHITE, WHITE, BLOCK],
    ],
)


TASK = Board(
    "Đề chính thức 9×9",
    [
        [
            BLOCK,
            BLOCK,
            Cell("clue", down=44),
            Cell("clue", down=16),
            Cell("clue", down=9),
            BLOCK,
            Cell("clue", down=15),
            Cell("clue", down=44),
            BLOCK,
        ],
        [
            BLOCK,
            Cell("clue", across=22),
            WHITE,
            WHITE,
            WHITE,
            Cell("clue", down=11, across=3),
            WHITE,
            WHITE,
            Cell("clue", down=14),
        ],
        [
            BLOCK,
            Cell("clue", down=17, across=28),
            WHITE,
            WHITE,
            WHITE,
            WHITE,
            WHITE,
            WHITE,
            WHITE,
        ],
        [
            Cell("clue", across=14),
            WHITE,
            WHITE,
            BLOCK,
            Cell("clue", down=12, across=20),
            WHITE,
            WHITE,
            WHITE,
            WHITE,
        ],
        [
            Cell("clue", across=17),
            WHITE,
            WHITE,
            Cell("clue", down=29, across=22),
            WHITE,
            WHITE,
            WHITE,
            WHITE,
            Cell("clue", down=7),
        ],
        [
            BLOCK,
            Cell("clue", down=12, across=28),
            WHITE,
            WHITE,
            WHITE,
            WHITE,
            Cell("clue", across=12),
            WHITE,
            WHITE,
        ],
        [
            Cell("clue", across=14),
            WHITE,
            WHITE,
            WHITE,
            WHITE,
            Cell("clue", down=7),
            Cell("clue", down=12, across=6),
            WHITE,
            WHITE,
        ],
        [
            Cell("clue", across=39),
            WHITE,
            WHITE,
            WHITE,
            WHITE,
            WHITE,
            WHITE,
            WHITE,
            BLOCK,
        ],
        [
            BLOCK,
            Cell("clue", across=16),
            WHITE,
            WHITE,
            Cell("clue", across=8),
            WHITE,
            WHITE,
            WHITE,
            BLOCK,
        ],
    ],
)


BOARDS = (DEMO, TASK)
