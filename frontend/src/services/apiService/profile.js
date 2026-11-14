import api from "./api";

export const BALANCE_CHANGE_EVENT = "balance-change";

export function notifyBalanceChanged() {
  window.dispatchEvent(new Event(BALANCE_CHANGE_EVENT));
}

export const getProfile = async (signal) => {
  const res = await api.get("/profile", { signal });
  return res.data;
};
