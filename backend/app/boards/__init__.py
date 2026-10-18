from boards.service import BoardService
from repositories import board_repo, task_repo, planning_repository


board_service = BoardService(board_repo, task_repo, planning_repository)
