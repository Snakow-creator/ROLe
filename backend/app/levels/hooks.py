from levels.data import xp_list


def current_level(xp):
    for i in range(len(xp_list)):
        # last level
        if i == len(xp_list):
            return xp_list[-1][1]
        # find current level
        elif xp_list[i][0] <= xp < xp_list[i+1][0]:
            return xp_list[i][1]
