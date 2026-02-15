from models.models import User

from users.requests import user_repo

from datetime import datetime, timezone


class UserService:
    @staticmethod
    async def load_data(name):
        # init object user, create data dict
        # return user and data in object
        user = await user_repo.get_by_name(name)

        data = {
            "name": user.name,
            "level": user.level,
            "xp": user.xp,
            "Spoints": user.Spoints,
            "days_streak": user.days_streak,
            "mul": user.mul,
            "sale_shop": user.sale_shop,
            "last_streak": user.last_streak.timestamp(),
            "last_mul": user.last_mul.timestamp(),
            "complete_simple_tasks": user.complete_simple_tasks,
            "complete_common_tasks": user.complete_common_tasks,
            "complete_hard_tasks": user.complete_hard_tasks,
            "complete_expert_tasks": user.complete_expert_tasks,
            "complete_hardcore_tasks": user.complete_hardcore_tasks,
        }

        return data


class WeeklyBonusService:
    @staticmethod
    async def claim(user: User):
        # get time
        time_now = datetime.now(timezone.utc)
        await user.update({
            "$inc": {"Spoints": 150, "xp": 150},
            "$set": {
                "penult_mul": user.mul,
                "penult_sale_shop": user.sale_shop,
                "penult_last_mul": user.last_mul,
                "last_mul": time_now,
                "mul": user.mul * 1.02, # x 2 % bonus
                "sale_shop": user.sale_shop * 0.985 # * 1 % sale bonus
            }
        })

    @staticmethod
    async def revoke(user: User):
        await user.update({
            "$inc": {"Spoints": 150, "xp": 150},
            "$set": {
                "last_mul": user.penult_last_mul,
                "mul": user.penult_mul,
                "sale_shop": user.penult_sale_shop, # * 1 % sale bonus
            }
        })
