from planning.service import PlanningService
from repositories import planning_repository, task_repo, board_repo


planning_service = PlanningService(planning_repository, task_repo, board_repo)
