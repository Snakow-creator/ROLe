from users.service import UserService
from users.weekly_bonus.service import WeeklyBonusService
from repositories import user_repo


user_service = UserService(user_repo)
weekly_bonus = WeeklyBonusService(user_repo)
