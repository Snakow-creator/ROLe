import assert from 'node:assert/strict';
import test from 'node:test';
import { mergeTaskRefresh, startTaskAutoRefresh } from './taskRefresh.js';

test('automatic refresh adds new tasks, removes expired ones and preserves Undo', () => {
  const previous = [
    { _id: 'expired', board_id: 'daily', completed: false },
    { _id: 'done', board_id: 'daily', completed: true },
    { _id: 'deleted-board', board_id: 'deleted', completed: true },
  ];
  const incoming = [{ _id: 'new', board_id: 'daily', completed: false }];
  const result = mergeTaskRefresh(previous, incoming, [{ _id: 'daily' }]);
  assert.deepEqual(result.map(task => task._id), ['new', 'done']);
  assert.equal(result[1].completed, true);
  assert.equal(previous.length, 3);
});

test('a task returned by the server takes precedence over a completed local copy', () => {
  const previous = [{ _id: 'task', board_id: 'daily', completed: true }];
  const incoming = [{ _id: 'task', board_id: 'daily', completed: false }];
  assert.deepEqual(mergeTaskRefresh(previous, incoming, [{ _id: 'daily' }]), incoming);
});

test('refresh runs each minute and on return or reconnect, pauses in hidden tabs and cleans up', () => {
  const documentTarget = new EventTarget();
  documentTarget.visibilityState = 'visible';
  const windowTarget = new EventTarget();
  let timerCallback;
  let stopped = false;
  windowTarget.setInterval = (callback, interval) => {
    timerCallback = callback;
    assert.equal(interval, 60_000);
    return 'timer';
  };
  windowTarget.clearInterval = timer => {
    assert.equal(timer, 'timer');
    stopped = true;
  };
  let refreshes = 0;
  const stop = startTaskAutoRefresh(() => { refreshes += 1; }, { documentTarget, windowTarget });
  timerCallback();
  assert.equal(refreshes, 1);
  documentTarget.visibilityState = 'hidden';
  timerCallback();
  windowTarget.dispatchEvent(new Event('focus'));
  assert.equal(refreshes, 1);
  documentTarget.visibilityState = 'visible';
  documentTarget.dispatchEvent(new Event('visibilitychange'));
  windowTarget.dispatchEvent(new Event('focus'));
  windowTarget.dispatchEvent(new Event('online'));
  assert.equal(refreshes, 4);
  stop();
  documentTarget.dispatchEvent(new Event('visibilitychange'));
  windowTarget.dispatchEvent(new Event('focus'));
  windowTarget.dispatchEvent(new Event('online'));
  assert.equal(refreshes, 4);
  assert.equal(stopped, true);
});
