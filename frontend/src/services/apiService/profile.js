import api from "./api";

export const getProfile = async (signal) => {
  const res = await api.get("/profile", { signal });
  return res.data;
};
