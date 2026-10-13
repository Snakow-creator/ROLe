list_baseBoards = ["simple", "common", "hard", "expert", "hardcore"]

task_bonus = 1.5  # + 50% of points

baseBoards_points = {
    "simple": 20,
    "common": 50,
    "hard": 200,
    "expert": 500,
    "hardcore": 5000,
}

baseBoards_data = (
    {
        "difficulty": "simple",
        "points": 20,
    },
    {
        "difficulty": "common",
        "points": 50,
    },
    {
        "difficulty": "hard",
        "points": 200,
    },
    {
        "difficulty": "expert",
        "points": 500,
    },
    {
        "difficulty": "hardcore",
        "points": 5000,
    },
)

# title -> (type, order, expire_days)
OLD_DEFAULT_BOARDS = {
  "Простые": ("simple", 0, 1),
  "Обычные": ("common", 1, 1),
  "Трудные": ("hard", 2, 7),
  "Сложные": ("expert", 3, 30),
  "Хардкорные": ("hardcore", 4, None),
}

