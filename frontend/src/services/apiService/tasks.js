import api from './api';
import { notifyBalanceChanged } from './profile';

export async function getTasks() {
  return api.get('/tasks');
}

export async function addTask(formData) {
  return api.post('/add/task', formData);
}

export async function completeTask({ id }) {
  const res = await api.put(`/complete/task/${id}`, {});
  notifyBalanceChanged();
  return res.data;
}

export async function unCompleteTask({ id }) {
  const res = await api.put(`/uncomplete/task/${id}`, {});
  notifyBalanceChanged();
  return res.data;
}

export async function deleteTask({ id }) {
  const res = await api.delete(`/delete/task/${id}`);
  return res.data;
}
