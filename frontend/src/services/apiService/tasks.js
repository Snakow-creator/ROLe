import api from "./api";


export const getTasks = async (creds) => {
  try {
    const res = await api.get("/tasks");
    creds.onFinish(res.data);


    return res
  } catch (error) {
    console.error(error);
  }
}


export async function addTask(formData) {
  try {
    const res = await api.post("/add/task", formData);
    return res

  } catch (error) {
    console.error(error);
    return false
  }
};


export async function completeTask(creds) {
  try {
    const res = await api.put(`/complete/task/${creds.id}`, {});
    // creds.onCompleteTask(res) уведомления

    return res
  } catch (error) {
    console.error(error);
    // creds.onError(error) уведомления
  }
}


export async function unCompleteTask(creds) {
  try {
    const res = await api.put(`/uncomplete/task/${creds.id}`, {});
    // creds.onUncompleteTask(res) уведомления

    return res
  } catch (error) {
    console.error(error);
    // creds.onError(error) уведомления
  }
}


export async function deleteTask(creds) {
  try {
    const res = await api.delete(`/delete/task/${creds.id}`);
    // creds.onDeleteTask(res.data.title); уведомления

    return res
  } catch (error) {
    console.error(error);
    // creds.onError(error) уведомления
  }
}
