import api from "./api";


export const fetchBuyItem = async (id) => {
  try {
    const res = await api.put(`/buy/item/${id}`);
    return res
  } catch (error) {
    console.log("свааааага")
    console.error(error);
    if (error.response?.status == 402) {
      const { message, notice } = error.response.data
      return {
        data: {
          "message": message,
          "notice": notice
        },
        status: 402
      }
    }
    console.error(error);
  }
}

export const fetchItems = async (creds) => {
  try {
    const res = await api.get("/items");
    creds.setCurrentItems(res.data);

  } catch (error) {
    console.error(error)
  }
};

export const addItem = async (formData) => {
  try {
    const res = await api.post("/add/item", formData);
    return res

  } catch (error) {
    console.error(error.response?.data || error.response?.data.message);
  }
}

export const  deleteItem = async (id) => {
  try {
    const res = await api.delete(`/delete/item/${id}`);
    return res
  } catch (error) {
    console.error(error);
  }
}
