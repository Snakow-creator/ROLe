from levels.data import xp_list


class LevelService:
    # check current level
    @staticmethod
    def current(xp):
        for i in range(len(xp_list)):
            # if xp more than last level
            if i == len(xp_list):
                return xp_list[-1][1]
            # find current level
            elif xp_list[i][0] <= xp < xp_list[i + 1][0]: # example 0 <= 199 < 300
                return xp_list[i][1] # return current level
