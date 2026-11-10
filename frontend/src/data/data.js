import BASE_URL from "../data/config.js";

export const filter_types_items = {
  "Всё": "all",
  "Отдых": "rest",
  "Деньги": "money",
  "Еда": "food",

}

export function avatarUrl(avatarId = "default_avatar_man") {
  return `${BASE_URL}avatars/${encodeURIComponent(avatarId)}.png`;
}
