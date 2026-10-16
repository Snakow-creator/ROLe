from levels.data import xp_list


class LevelService:
    # check current level
    @staticmethod
    def current(xp):
        for required_xp, level in reversed(xp_list):
            if xp >= required_xp:
                return level
        return xp_list[0][1]
