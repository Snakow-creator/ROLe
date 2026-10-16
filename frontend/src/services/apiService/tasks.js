import api from './api';

export async function getTasks() {
  return api.get('/tasks');
}

export async function addTask(formData) {
  return api.post('/add/task', formData);
}

export async function completeTask({ id }) {
  const res = await api.put(`/complete/task/${id}`, {});
  return res.data;
}

export async function unCompleteTask({ id }) {
  const res = await api.put(`/uncomplete/task/${id}`, {});
  return res.data;
}

export async function deleteTask({ id }) {
  const res = await api.delete(`/delete/task/${id}`);
  return res.data;
}
