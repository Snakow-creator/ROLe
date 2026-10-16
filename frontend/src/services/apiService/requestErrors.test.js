import assert from 'node:assert/strict';
import test from 'node:test';
import { getRequestErrorMessage, isSessionExpiredError } from './requestErrors.js';

function requestError(status, detail, headers = { Authorization: 'Bearer test-token' }, url = '/tasks') {
  return { response: { status, data: { detail } }, config: { headers, url } };
}

test('a network error explains that the local server is unreachable', () => {
  assert.match(getRequestErrorMessage(new Error('Network Error'), 'Ошибка'), /Нет связи с сервером/);
});

for (const [status, detail, expected] of [
  [409, 'Task has expired', /Срок выполнения квеста истёк/],
  [409, 'Task already completed', /Квест уже выполнен/],
  [409, 'Task is not completed', /уже отменено/],
  [409, 'Task is not active', /пока недоступен/],
  [404, 'Board not found', /Доска больше недоступна/],
  [404, 'Task not found', /Квест больше недоступен/],
  [401, 'Unauthorized, this task is not your', /нет доступа к этому квесту/],
  [401, 'Token expired', /Войдите в аккаунт/],
  [403, 'Forbidden', /нет доступа к этому действию/],
  [422, [{ loc: ['body', 'title'], msg: 'Invalid' }], /Проверьте данные квеста/],
  [503, 'Private server stack trace', /Сервер временно недоступен/],
]) {
  test(`HTTP ${status}: ${JSON.stringify(detail)}`, () => {
    assert.match(getRequestErrorMessage(requestError(status, detail), 'Ошибка'), expected);
  });
}

test('unknown errors use the action-specific fallback, without exposing server details', () => {
  assert.equal(getRequestErrorMessage(requestError(409, 'Private error details'), 'Повторите действие'), 'Повторите действие');
});

test('an unauthorized authenticated request requires a new session', () => {
  assert.equal(isSessionExpiredError(requestError(401, 'Token expired')), true);
  assert.equal(isSessionExpiredError(requestError(401, 'Invalid token', { authorization: 'Bearer invalid' })), true);
});

test('permission errors do not claim that the session expired', () => {
  assert.equal(isSessionExpiredError(requestError(401, 'Unauthorized, this task is not your')), false);
  assert.equal(isSessionExpiredError(requestError(403, 'Forbidden')), false);
});

test('requests without a token, login errors and connection failures do not mean session expiration', () => {
  assert.equal(isSessionExpiredError(requestError(401, 'Missing token', {})), false);
  for (const url of ['/login', '/register', '/logout', '/login?redirect=/quests']) {
    assert.equal(isSessionExpiredError(requestError(401, 'Invalid credentials', { Authorization: 'Bearer old' }, url)), false);
  }
  assert.equal(isSessionExpiredError(new Error('Network Error')), false);
});
