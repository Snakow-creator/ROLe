import { useEffect, useRef, useState } from 'react';
import PlanDialog from './PlanDialog';
import { getPlanErrorMessage } from '../../services/apiService/plan';
import { weekDays, weekMonday } from '../../services/apiService/planDates';

const inputClass = 'mt-1 w-full rounded-xl border border-[#DDE3EC] bg-white px-3 py-2.5 text-sm font-normal text-[#1E293B] outline-none focus:border-orange-400 focus:ring-2 focus:ring-orange-100 disabled:bg-[#F2F4F7]';

export default function PlanEntryDialog({ entry, kind = 'task', day, week, today, goalId, goals, boards, onSave, onDelete, onClose }) {
  const isGoal = (entry?.kind || kind) === 'goal';
  const selectedGoal = goals.find(goal => goal._id === goalId);
  const historical = week < weekMonday(today);
  const [form, setForm] = useState({
    title: entry?.title || '', description: entry?.description || '',
    day: entry?.day || day, time: entry?.time || '', end_time: entry?.end_time || '',
    board_id: entry?.board_id || '',
    goal_id: goals.some(goal => goal._id === entry?.goal_id) ? entry.goal_id : goalId || '',
    repeat: entry ? entry.repeating : selectedGoal ? selectedGoal.repeating : !historical,
    scope: 'single',
  });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [confirmDelete, setConfirmDelete] = useState(false);
  const pendingRef = useRef(false);
  const titleRef = useRef(null);
  const locked = !isGoal && Boolean(entry?.completed);
  const title = entry ? (isGoal ? 'Недельная цель' : 'Задача плана') : (isGoal ? 'Новая цель недели' : 'Новая задача');

  useEffect(() => { titleRef.current?.focus(); }, []);

  const change = event => {
    const { name, value, type, checked } = event.target;
    setForm(current => ({ ...current, [name]: type === 'checkbox' ? checked : value }));
    setError('');
    setConfirmDelete(false);
  };

  const perform = async action => {
    if (pendingRef.current) return;
    pendingRef.current = true;
    setBusy(true);
    setError('');
    try {
      await action();
      onClose();
    } catch (requestError) {
      setError(getPlanErrorMessage(requestError));
    } finally {
      pendingRef.current = false;
      setBusy(false);
    }
  };

  const submit = event => {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    const startTime = fields.get('time') || null;
    const endTime = fields.get('end_time') || null;
    if (!form.title.trim()) { setError('Введите название.'); return; }
    if (endTime && (!startTime || endTime <= startTime)) { setError('Время окончания должно быть позже начала.'); return; }
    perform(() => onSave({
      kind: isGoal ? 'goal' : 'task', title: form.title.trim(), description: form.description,
      day: isGoal ? week : form.day,
      time: isGoal ? null : startTime,
      end_time: isGoal ? null : endTime,
      board_id: isGoal ? null : form.board_id || null,
      goal_id: isGoal ? null : form.goal_id || null,
      repeat: form.repeat, scope: form.scope,
    }, entry?._id));
  };

  return (
    <PlanDialog title={title} onClose={onClose} busy={busy}>
      <form onSubmit={submit}>
        {locked && <p className="mb-4 rounded-xl bg-green-50 p-3 text-sm leading-6 text-green-800">Задача выполнена. Для редактирования сначала отмените выполнение.</p>}
        <fieldset disabled={busy || locked} className="space-y-4 disabled:opacity-65">
          <label className="block text-sm font-semibold">Название
            <textarea ref={titleRef} name="title" required maxLength={100} rows={2} value={form.title} onChange={change} placeholder={isGoal ? 'Чего хочешь достичь за неделю?' : 'Что запланируем?'} className={`${inputClass} resize-none`} />
          </label>
          <label className="block text-sm font-semibold">Описание <span className="font-normal text-[#94A3B8]">· необязательно</span>
            <textarea name="description" maxLength={255} rows={3} value={form.description} onChange={change} placeholder="Детали, заметки и ожидаемый результат" className={`${inputClass} resize-y`} />
          </label>
          {!isGoal && <>
            <label className="block text-sm font-semibold">День недели
              <select name="day" value={form.day} onChange={change} className={inputClass}>
                {weekDays(week).map(item => <option key={item.day} value={item.day}>{item.title} · {item.day.slice(8)}.{item.day.slice(5, 7)}</option>)}
              </select>
            </label>
            <div className="grid grid-cols-2 gap-3">
              <label className="block text-sm font-semibold">Начало
                <input type="time" name="time" value={form.time} onInput={change} onChange={change} className={inputClass} />
              </label>
              <label className="block text-sm font-semibold">Окончание
                <input type="time" name="end_time" value={form.end_time} onInput={change} onChange={change} className={inputClass} />
              </label>
            </div>
            <label className="block text-sm font-semibold">Часть недельной цели
              <select name="goal_id" value={form.goal_id} onChange={change} className={inputClass}>
                <option value="">Самостоятельная задача</option>
                {goals.map(goal => <option key={goal._id} value={goal._id}>{goal.title}</option>)}
              </select>
            </label>
            <div className="rounded-xl border border-[#E5E9F0] bg-[#FAFBFF] p-3">
              <label className="flex cursor-pointer items-center gap-2 text-sm font-semibold">
                <input type="checkbox" checked={Boolean(form.board_id)} disabled={!boards.length} onChange={event => setForm(current => ({ ...current, board_id: event.target.checked ? boards[0]?._id || '' : '' }))} className="h-4 w-4 accent-orange-500" />
                Создавать квест с наградой
              </label>
              {form.board_id ? <label className="mt-3 block text-xs text-[#64748B]">Доска квестов
                <select name="board_id" value={form.board_id} onChange={change} className={inputClass}>
                  {boards.map(board => <option key={board._id} value={board._id}>{board.title} · {board.award_points} Spoints · {board.award_xp} XP</option>)}
                </select>
                <span className="mt-2 block leading-5">Квест появится с начала назначенного дня. Время выше — ориентир для расписания, МСК.</span>
              </label> : <p className="mt-2 text-xs leading-5 text-[#64748B]">{boards.length ? 'Задача останется в плане и не будет начислять XP и Spoints.' : 'Сначала создайте доску в разделе «Мои квесты», чтобы назначать награды.'}</p>}
            </div>
          </>}
          {entry?.template_id && <fieldset className="space-y-2 rounded-xl bg-[#F2F4F7] p-3">
            <legend className="px-1 text-xs font-semibold text-[#64748B]">Применить изменения</legend>
            <label className="flex items-center gap-2 text-sm"><input type="radio" name="scope" value="single" checked={form.scope === 'single'} onChange={change} className="accent-orange-500" />Только к этой {isGoal ? 'цели' : 'задаче'}</label>
            <label className="flex items-center gap-2 text-sm"><input type="radio" name="scope" value="future" checked={form.scope === 'future'} onChange={change} disabled={historical} className="accent-orange-500" />К этой и последующим повторениям</label>
          </fieldset>}
          <label className="flex items-center gap-2 text-sm font-semibold">
            <input type="checkbox" name="repeat" checked={form.repeat} onChange={change} disabled={historical || (Boolean(entry?.template_id) && form.scope === 'single')} className="h-4 w-4 accent-orange-500" />
            Повторять каждую неделю
          </label>
          <p className="text-xs leading-5 text-[#7C8AA0]">{isGoal ? 'Цель хранится в «Целях». Добавь её части в дни недели — они заполнят полоску прогресса.' : 'Следующая неделя получит отдельную невыполненную задачу. История предыдущей недели сохранится.'}</p>
        </fieldset>
        {error && <p role="alert" className="mt-4 rounded-xl bg-red-50 p-3 text-sm leading-6 text-red-700">{error}</p>}
        {confirmDelete && <p className="mt-4 text-sm leading-6 text-red-700">{isGoal ? 'Цель будет удалена, а её задачи останутся в расписании.' : 'Задача будет отменена. Если она входит в цель, её сегмент сохранится; задачу можно восстановить из «Целей».'}</p>}
        <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
          {entry && !entry.cancelled ? <button type="button" disabled={busy || locked} onClick={() => confirmDelete ? perform(() => onDelete(entry._id, form.scope)) : setConfirmDelete(true)} className="cursor-pointer rounded-lg px-3 py-2 text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-40">{confirmDelete ? 'Подтвердить удаление' : 'Удалить'}</button> : <span />}
          <div className="flex gap-2">
            <button type="button" disabled={busy} onClick={onClose} className="cursor-pointer rounded-xl border border-[#E5E9F0] px-4 py-2.5 text-sm font-semibold hover:bg-[#F2F4F7] disabled:opacity-40">Закрыть</button>
            <button type="submit" disabled={busy || locked} className="cursor-pointer rounded-xl bg-orange-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-orange-600 disabled:opacity-40">{busy ? 'Сохраняем…' : entry ? 'Сохранить' : 'Добавить'}</button>
          </div>
        </div>
      </form>
    </PlanDialog>
  );
}
