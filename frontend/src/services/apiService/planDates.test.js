import assert from 'node:assert/strict';
import test from 'node:test';
import { moscowToday, shiftDay, weekDays, weekLabel, weekMonday } from './planDates.js';

test('the plan follows Moscow midnight, independently of browser timezone', () => {
  assert.equal(moscowToday(new Date('2026-10-15T20:59:59Z')), '2026-10-15');
  assert.equal(moscowToday(new Date('2026-10-15T21:00:00Z')), '2026-10-16');
});

test('week navigation crosses months and years without timezone shifts', () => {
  assert.equal(weekMonday('2027-01-03'), '2026-12-28');
  assert.equal(shiftDay('2026-12-28', 7), '2027-01-04');
  assert.equal(shiftDay('2026-03-02', -7), '2026-02-23');
  const days = weekDays('2026-12-28');
  assert.equal(days.length, 7);
  assert.deepEqual(days[0], { title: 'Понедельник', day: '2026-12-28' });
  assert.deepEqual(days[6], { title: 'Воскресенье', day: '2027-01-03' });
  assert.match(weekLabel('2026-12-28'), /2026/);
  assert.match(weekLabel('2026-12-28'), /2027/);
});

test('invalid URL dates fall back to the current week', () => {
  assert.equal(weekMonday('2026-99-99'), weekMonday());
  assert.equal(weekMonday('2026-02-30'), weekMonday());
});
