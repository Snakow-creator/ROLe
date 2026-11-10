import api from "./api";

export const selectAvatar = async (avatarId) => {
  const res = await api.put("/profile/avatar", { avatar_id: avatarId });
  return res.data.avatar;
};
