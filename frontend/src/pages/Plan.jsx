import { useCallback, useEffect, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import PlanEntryDialog from '../components/plan/PlanEntryDialog';
import GoalsDialog, { GoalProgress } from '../components/plan/GoalsDialog';
import Spinner from '../components/Spinner';
import { getPlan, savePlanEntry, cancelPlanEntry, restorePlanEntry, completePlanEntry, copyPlanWeek, getPlanErrorMessage } from '../services/apiService/plan';
import { moscowToday, shiftDay, weekDays, weekLabel, weekMonday } from '../services/apiService/planDates';
import { startTaskAutoRefresh } from '../services/apiService/taskRefresh';
import { useNotify } from '../context/NotificationContext';
import { TaskSubmitNotification } from '../components/webNotifications/types/TaskNotification';
import { TaskUnSubmitNotification } from '../components/webNotifications/types/TaskUnSubmitNotification';
import { UpLevelNotification } from '../components/webNotifications/types/UpLevelNotification';
import { DownLevelNotification } from '../components/webNotifications/types/DownLevelNotification';
import { WeeklyBonusNotification } from '../components/webNotifications/types/WeeklyBonusNotification';
import { RevokeWeeklyBonusNotification } from '../components/webNotifications/types/RevokeWeeklyBonusNotification';
import { isSessionExpiredError } from '../services/apiService/requestErrors';


export default function Plan() {
  const [searchParams, setSearchParams] = useSearchParams();
  const week = weekMonday(searchParams.get('week') || moscowToday());
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [editor, setEditor] = useState(null);
  const [goalsOpen, setGoalsOpen] = useState(false);
  const [copyMessage, setCopyMessage] = useState('');
  const requestRef = useRef(0);
  const inFlightRef = useRef(0);
  const mutationRef = useRef(false);
  const pausedRef = useRef(false);
  const activeWeekRef = useRef(week);
  const { push } = useNotify();

  const load = useCallback(async ({ background = false } = {}) => {
    if (activeWeekRef.current !== week) return;
    if (background && (inFlightRef.current || mutationRef.current || pausedRef.current)) return;
    const request = ++requestRef.current;
    inFlightRef.current += 1;
    try {
      const result = await getPlan(week);
      if (request !== requestRef.current) return;
      setPlan(result);
      setError('');
      pausedRef.current = false;
      return result;
    } catch (requestError) {
      if (request !== requestRef.current) return;
      if (isSessionExpiredError(requestError)) pausedRef.current = true;
      if (!background) setError(getPlanErrorMessage(requestError));
    } finally {
      inFlightRef.current -= 1;
      if (request === requestRef.current) setLoading(false);
    }
  }, [week]);

  useEffect(() => {
    activeWeekRef.current = week;
    load();
    const stop = startTaskAutoRefresh(() => load({ background: true }));
    return () => { stop(); requestRef.current += 1; };
  }, [load, week]);

  const navigateWeek = next => {
    if (mutationRef.current) return;
    setEditor(null);
    setGoalsOpen(false);
    setCopyMessage('');
    setLoading(true);
    setSearchParams({ week: next });
  };

  const mutate = async action => {
    if (mutationRef.current) return;
    mutationRef.current = true;
    requestRef.current += 1;
    setBusy(true);
    setError('');
    try {
      const result = await action();
      await load();
      return result;
    } finally {
      mutationRef.current = false;
      setBusy(false);
    }
  };

  const toggle = async entry => {
    if (mutationRef.current) return;
    try {
      const result = await mutate(() => completePlanEntry(entry._id, !entry.completed));
      if (result.notice) push(entry.completed ? new TaskUnSubmitNotification(result.notice) : new TaskSubmitNotification(result.notice));
      const notices = [
        ['notice_up_level', UpLevelNotification], ['notice_down_level', DownLevelNotification],
        ['notice_weekly_claim_bonus', WeeklyBonusNotification], ['notice_weekly_revoke_bonus', RevokeWeeklyBonusNotification],
      ];
      notices.forEach(([key, Notice]) => { if (result[key]) push(new Notice(result[key])); });
    } catch (requestError) {
      setError(getPlanErrorMessage(requestError));
    }
  };

  const restore = async entry => {
    try { await mutate(() => restorePlanEntry(entry._id)); }
    catch (requestError) { setError(getPlanErrorMessage(requestError)); }
  };

  const copy = async () => {
    try {
      const result = await mutate(() => copyPlanWeek(week));
      if (!result) return;
      navigateWeek(result.week_start);
      setCopyMessage(result.copied ? `План перенесён. Добавлено записей: ${result.copied}.` : 'План следующей недели уже подготовлен. Твои изменения сохранены.');
    } catch (requestError) { setError(getPlanErrorMessage(requestError)); }
  };

  const currentPlan = plan?.week_start === week ? plan : null;
  const today = currentPlan?.today || moscowToday();
  const newEntry = (kind, day, goalId) => {
    if (!mutationRef.current) setEditor({ kind, day, goalId, week });
  };
  const edit = entry => {
    if (!mutationRef.current) setEditor({ entry, kind: entry.kind, day: entry.day, week });
  };
  const defaultDay = today >= week && today <= shiftDay(week, 6) ? today : week;
  const tasks = (currentPlan?.entries || []).filter(entry => !entry.cancelled);
  const goals = currentPlan?.goals || [];
  const boards = currentPlan?.boards || [];

  return (
    <section className="flex h-[calc(100dvh-57px)] min-h-[520px] flex-col gap-4 p-3 md:p-5" aria-label="План недели">
      <div className="flex shrink-0 flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-extrabold md:text-2xl">План недели</h1>
          <p className="mt-1 text-xs text-[#7C8AA0]">Твоё время, шаги и цели · МСК</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center rounded-xl border border-[#DDE3EC] bg-white p-1 shadow-sm">
            <button type="button" disabled={busy} onClick={() => navigateWeek(shiftDay(week, -7))} aria-label="Предыдущая неделя" className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-lg text-xl hover:bg-[#F2F4F7] disabled:opacity-40">‹</button>
            <span className="px-2 text-center text-xs font-bold sm:text-sm">{weekLabel(week)}</span>
            <button type="button" disabled={busy} onClick={() => navigateWeek(shiftDay(week, 7))} aria-label="Следующая неделя" className="flex h-9 w-9 cursor-pointer items-center justify-center rounded-lg text-xl hover:bg-[#F2F4F7] disabled:opacity-40">›</button>
          </div>
          <button type="button" disabled={busy || week === weekMonday(today)} onClick={() => navigateWeek(weekMonday(today))} className="cursor-pointer rounded-xl border border-[#DDE3EC] bg-white px-3 py-3 text-xs font-semibold hover:bg-[#FAFBFF] disabled:opacity-40">Сегодня</button>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" disabled={busy || !currentPlan} onClick={copy} title="Скопировать задачи и цели в следующую неделю, сохранив уже созданные" className="cursor-pointer rounded-xl border border-[#DDE3EC] bg-white px-3 py-3 text-xs font-semibold hover:bg-[#FAFBFF] disabled:opacity-40">На следующую неделю →</button>
          <button type="button" disabled={busy || !currentPlan} onClick={() => setGoalsOpen(true)} className="cursor-pointer rounded-xl bg-orange-500 px-5 py-3 text-sm font-bold text-white shadow-sm hover:bg-orange-600 disabled:opacity-40">Цели <span className="ml-1 rounded-md bg-white/20 px-1.5 py-0.5 text-xs">{goals.length}</span></button>
        </div>
      </div>

      {error && <div role="alert" className="flex shrink-0 flex-wrap items-center justify-between gap-2 rounded-xl border border-red-100 bg-red-50 p-3 text-sm text-red-700"><p>{error}</p><button type="button" onClick={() => load()} className="cursor-pointer font-bold underline">Обновить</button></div>}
      {copyMessage && <p role="status" className="shrink-0 rounded-xl border border-green-100 bg-green-50 p-3 text-sm text-green-800">{copyMessage}</p>}

      {loading || !currentPlan ? <div className="flex flex-1 items-center justify-center">{loading ? <Spinner /> : <p className="text-sm text-[#7C8AA0]">План пока не загружен.</p>}</div> : <div className="min-h-0 flex-1 overflow-x-auto pb-1">
        <div className="grid h-full min-w-[2032px] grid-cols-7 gap-3">
          {weekDays(week).map(({ day, title }, index) => {
            const entries = tasks.filter(entry => entry.day === day).sort((a, b) => (a.time || '99:99').localeCompare(b.time || '99:99') || a._id.localeCompare(b._id));
            const isToday = day === today;
            return <section key={day} aria-label={title} className={`flex min-h-0 flex-col rounded-2xl border bg-[#FAFBFF] shadow-sm ${isToday ? 'border-orange-300 ring-1 ring-orange-200' : 'border-[#E0E5ED]'}`}>
              <div className="flex shrink-0 items-center justify-between gap-2 border-b border-[#E5E9F0] p-4">
                <div>
                  <h2 className={`text-xs font-bold ${isToday ? 'text-orange-600' : index > 4 ? 'text-[#94A3B8]' : 'text-[#64748B]'}`}>{title}</h2>
                  <div className="mt-2 flex items-center gap-2"><span className={`flex h-9 w-9 items-center justify-center rounded-xl text-xl font-extrabold ${isToday ? 'bg-orange-500 text-white' : 'text-[#334155]'}`}>{Number(day.slice(8))}</span>{isToday && <span className="text-[10px] font-bold text-orange-600">Сегодня</span>}</div>
                </div>
                <span className="rounded-lg bg-[#EEF2F7] px-2 py-1 text-xs text-[#7C8AA0]">{entries.length}</span>
              </div>
              <div className="min-h-0 flex-1 space-y-2 overflow-y-auto p-2.5">
                {!entries.length && <p className="rounded-xl border border-dashed border-[#E5E9F0] px-3 py-6 text-center text-xs leading-5 text-[#A0AABB]">Свободный день<br />Добавь первый план</p>}
                {entries.map(entry => {
                  const goal = goals.find(item => item._id === entry.goal_id);
                  return <article key={entry._id} className={`rounded-xl border bg-white p-3 shadow-sm ${entry.completed ? 'border-green-100' : 'border-[#E5E9F0]'}`}>
                    <div className="flex items-start gap-2">
                      <button type="button" onClick={() => toggle(entry)} disabled={busy || day > today || (entry.inactive && !entry.completed)} aria-label={`${entry.completed ? 'Отменить выполнение' : 'Выполнить'} «${entry.title}»`} aria-pressed={entry.completed} className={`mt-0.5 flex h-4 w-4 shrink-0 cursor-pointer items-center justify-center rounded-full border text-[10px] disabled:cursor-default disabled:opacity-40 ${entry.completed ? 'border-green-400 bg-green-400 text-white' : 'border-[#CBD5E1] hover:border-orange-400'}`}>{entry.completed && '✓'}</button>
                      <button type="button" onClick={() => edit(entry)} className={`min-w-0 cursor-pointer break-words text-left text-[13px] font-bold leading-6 hover:text-orange-600 ${entry.completed ? 'text-[#94A3B8] line-through' : ''}`}>{entry.title}</button>
                    </div>
                    <div className="mt-2 flex flex-wrap items-center gap-1.5 text-[10px]">
                      {entry.time && <span className="rounded-md bg-orange-50 px-1.5 py-1 font-bold text-orange-700">{entry.time}{entry.end_time && `–${entry.end_time}`}</span>}
                      {entry.repeating && <span title="Повторяется каждую неделю" className="text-sm text-[#94A3B8]">↻</span>}
                      {entry.inactive && !entry.completed && <span className="text-red-500">Срок истёк</span>}
                      {entry.board_id ? <span className="rounded-md bg-blue-50 px-1.5 py-1 text-blue-600">{boards.find(board => board._id === entry.board_id)?.title || entry.board_title || 'Квест'}</span> : <span className="text-[#94A3B8]">Без награды</span>}
                    </div>
                    {goal && <div className="mt-3 border-t border-[#F1F4F8] pt-2"><button type="button" onClick={() => setGoalsOpen(true)} className="mb-2 block max-w-full cursor-pointer truncate text-left text-[10px] font-semibold text-[#94A3B8] hover:text-orange-600">{goal.title} · {goal.done}/{goal.total}</button><GoalProgress goal={goal} compact /></div>}
                  </article>;
                })}
              </div>
              <button type="button" disabled={busy} onClick={() => newEntry('task', day)} className="m-2.5 mt-0 shrink-0 cursor-pointer rounded-xl px-3 py-2.5 text-left text-xs font-semibold text-[#7C8AA0] hover:bg-[#EEF2F7] hover:text-orange-600 disabled:opacity-40">＋ Добавить задачу</button>
            </section>;
          })}
        </div>
      </div>}

      {goalsOpen && <GoalsDialog goals={goals} today={today} busy={busy} onClose={() => setGoalsOpen(false)} onCreate={() => newEntry('goal', week)} onEdit={edit} onAddPart={goal => newEntry('task', defaultDay, goal._id)} onToggle={toggle} onRestore={restore} />}
      {editor?.week === week && <PlanEntryDialog key={editor.entry?._id || `${editor.kind}-${editor.day}-${editor.goalId || ''}`} {...editor} week={week} today={today} goals={goals} boards={boards} onSave={(data, id) => mutate(() => savePlanEntry(data, id))} onDelete={(id, scope) => mutate(() => cancelPlanEntry(id, scope))} onClose={() => setEditor(null)} />}
    </section>
  );
}
