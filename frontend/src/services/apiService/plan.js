import api from './api';
import { getRequestErrorMessage } from './requestErrors';

export async function getPlan(week) {
  return (await api.get('/plan', { params: { week }, timeout: 15_000 })).data;
}

export async function savePlanEntry(data, id) {
  return (await (id ? api.put(`/plan/entries/${id}`, data) : api.post('/plan/entries', data))).data;
}

export async function cancelPlanEntry(id, scope) {
  return (await api.delete(`/plan/entries/${id}`, { params: { scope } })).data;
}

export async function restorePlanEntry(id) {
  return (await api.post(`/plan/entries/${id}/restore`)).data;
}

export async function completePlanEntry(id, completed) {
  return (await api.put(`/plan/entries/${id}/completion`, { completed })).data;
}

export async function copyPlanWeek(week) {
  return (await api.post('/plan/copy', null, { params: { week } })).data;
}

const planMessages = {
  'Plan entry not found': 'Задача плана больше недоступна. Обновите неделю.',
  'Choose an active goal from the same week': 'Выберите действующую цель этой недели.',
  'A repeating task requires a repeating goal': 'Для повторяющейся части выберите повторяющуюся цель или отключите повторение.',
  'Keep the entry kind and choose a day from the same week': 'Выберите день в пределах открытой недели.',
  'Change future repetitions from the current or a future week': 'Последующие повторения можно менять из текущей или будущей недели.',
  'Undo completion before editing the task': 'Сначала отмените выполнение задачи, затем отредактируйте её.',
  'Undo completion before deleting the task': 'Сначала отмените выполнение задачи, затем удалите её.',
  'This plan entry cannot be completed': 'Эта задача отменена. Сначала восстановите её.',
};

export function getPlanErrorMessage(error) {
  const detail = error.response?.data?.detail;
  if (typeof detail === 'string' && Object.hasOwn(planMessages, detail)) return planMessages[detail];
  return getRequestErrorMessage(error, 'Не удалось обновить план. Повторите попытку.');
}
