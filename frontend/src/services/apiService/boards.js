import api from "./api";

export async function createBoard(data) {
  const res = await api.post("/add/board", data);
  return res.data.board;
}
