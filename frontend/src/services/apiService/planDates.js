export const WEEKDAYS = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье'];

export function moscowToday(now = new Date()) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Europe/Moscow', year: 'numeric', month: '2-digit', day: '2-digit',
  }).formatToParts(now);
  const values = Object.fromEntries(parts.map(part => [part.type, part.value]));
  return `${values.year}-${values.month}-${values.day}`;
}

export function shiftDay(day, offset) {
  const date = new Date(`${day}T12:00:00Z`);
  date.setUTCDate(date.getUTCDate() + offset);
  return date.toISOString().slice(0, 10);
}

export function weekMonday(day = moscowToday()) {
  const date = new Date(`${day}T12:00:00Z`);
  if (!/^\d{4}-\d{2}-\d{2}$/.test(day) || Number.isNaN(date.valueOf()) || date.toISOString().slice(0, 10) !== day) {
    return weekMonday(moscowToday());
  }
  return shiftDay(day, -((date.getUTCDay() + 6) % 7));
}

export function weekDays(week) {
  return WEEKDAYS.map((title, index) => ({ title, day: shiftDay(week, index) }));
}

export function weekLabel(week) {
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC',
  }).formatRange(new Date(`${week}T12:00:00Z`), new Date(`${shiftDay(week, 6)}T12:00:00Z`));
}
