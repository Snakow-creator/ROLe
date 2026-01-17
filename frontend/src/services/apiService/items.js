import api from "./api";


export const fetchBuyItem = async (id) => {
  try {
    const res = await api.put(`/buy/item/${id}`);
    return res
  } catch (error) {
    console.error(error);
  }
}

export const fetchItems = async (setCurrentItems) => {
  try {
    const res = await api.get("/items");
    setCurrentItems(res.data);

  } catch (error) {
    console.error(error)
  }
};

export const addItem = async (formData) => {
  try {
    const res = await api.post("/add/item", formData);
    return res

  } catch (error) {
    console.error(error);
  }
}

export const deleteItem = async (id) => {
  try {
    const res = await api.delete(`/delete/item/${id}`);
    return res
  } catch (error) {
    console.error(error);
  }
}
