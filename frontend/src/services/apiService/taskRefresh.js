export function mergeTaskRefresh(previous, incoming, boards) {
  const incomingIds = new Set(incoming.map(task => task._id));
  const boardIds = new Set(boards.map(board => board._id));
  // Preserve the current page's completed cards so automatic refresh keeps Undo available.
  const completed = previous.filter(task =>
    task.completed && boardIds.has(task.board_id) && !incomingIds.has(task._id)
  );
  return [...incoming, ...completed];
}

export function startTaskAutoRefresh(refresh, {
  documentTarget = document,
  windowTarget = window,
  interval = 60_000,
} = {}) {
  const refreshVisible = () => {
    if (documentTarget.visibilityState === 'visible') refresh();
  };
  const timer = windowTarget.setInterval(refreshVisible, interval);
  documentTarget.addEventListener('visibilitychange', refreshVisible);
  windowTarget.addEventListener('focus', refreshVisible);
  windowTarget.addEventListener('online', refreshVisible);

  return () => {
    windowTarget.clearInterval(timer);
    documentTarget.removeEventListener('visibilitychange', refreshVisible);
    windowTarget.removeEventListener('focus', refreshVisible);
    windowTarget.removeEventListener('online', refreshVisible);
  };
}
