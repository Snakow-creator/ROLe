import api from "./api";

export async function createBoard(data) {
  const res = await api.post("/add/board", data);
  return res.data.board;
}

export async function deleteBoard(id) {
  const res = await api.delete(`/delete/board/${id}`);
  return res.data;
}
