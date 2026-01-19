import api from "./api";

export const getAvatar = async (onUpdateAvatar) => {
  const res = await api.get("/users/avatar")

  onUpdateAvatar(res.data)
}
