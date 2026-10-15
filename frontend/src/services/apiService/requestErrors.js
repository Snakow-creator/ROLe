const taskMessages = {
  'Board not found': 'Доска больше недоступна. Обновите список досок.',
  'Task not found': 'Квест больше недоступен. Обновите список квестов.',
  'Task has expired': 'Срок выполнения квеста истёк.',
  'Task is not active': 'Квест пока недоступен или срок его выполнения истёк.',
  'Task already completed': 'Квест уже выполнен. Обновите список квестов.',
  'Task is not completed': 'Выполнение этого квеста уже отменено. Обновите список квестов.',
  'Unauthorized, this task is not your': 'У вас нет доступа к этому квесту.',
};

export function getRequestErrorMessage(error, fallback) {
  const status = error.response?.status;
  const detail = error.response?.data?.detail;
  if (!error.response) return 'Нет связи с сервером. Проверьте подключение и повторите попытку.';
  if (typeof detail === 'string' && Object.hasOwn(taskMessages, detail)) return taskMessages[detail];
  if (status === 401) return 'Войдите в аккаунт, чтобы продолжить.';
  if (status === 403) return 'У вас нет доступа к этому действию.';
  if (status === 422) return 'Проверьте данные квеста и повторите попытку.';
  if (status >= 500) return 'Сервер временно недоступен. Попробуйте ещё раз.';
  return fallback;
}

export function isSessionExpiredError(error) {
  const { response, config } = error;
  const authorization = config?.headers?.Authorization || config?.headers?.authorization;
  const authPath = config?.url?.split('?')[0];
  return response?.status === 401 && Boolean(authorization)
    && !['/login', '/register', '/logout'].includes(authPath)
    && response.data?.detail !== 'Unauthorized, this task is not your';
}
