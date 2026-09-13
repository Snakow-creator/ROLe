from models.models import User

from users.requests import user_repo

from datetime import datetime, timezone
from notices import web_notice



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

        mul = round(user.mul, 2)
        sale_shop = round(user.sale_shop, 2)

        return web_notice(
            title="Вы получили недельный бонус! 🎉",
            message=f"Ваш множитель опыта теперь снова {mul}%, а скидка магазина {sale_shop}%, а Xp и Spoints увеличены на 150",
            type="claim_weekly_bonus",
        )

    # return bonus to previus state
    @staticmethod
    async def revoke(user: User):
        await user.update({
            "$inc": {"Spoints": 150, "xp": 150},
            "$set": {
                "last_mul": user.penult_last_mul,
                "mul": user.penult_mul,
                "sale_shop": user.penult_sale_shop,
            }
        })

        mul = round(user.mul, 2)
        sale_shop = round(user.sale_shop, 2)

        return web_notice(
            title="Ваш бонус недели снят",
            message=f"Ваш множитель опыта теперь снова {mul}%, а скидка магазина {sale_shop}%, а Xp и Spoints вернулись к прежнему уровню",
            task="revoke_weekly_bonus",
        )

async def delete_task(task):
    notice = web_notice(
        title=f"Задача {task.title} удалена",
        type="delete_task"
    )

    return {
        "message": "Task deleted",
        "title": task.title,
        "notice": notice.model_dump(),
    }
