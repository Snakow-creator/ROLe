from tasks.service import TaskService
from repositories import task_repo, board_repo, user_repo, planning_repository


task_service = TaskService(task_repo, board_repo, user_repo, planning_repository)
