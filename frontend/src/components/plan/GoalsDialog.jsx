import PlanDialog from './PlanDialog';

export function GoalProgress({ goal, compact = false }) {
  return (
    <div>
      <div role="progressbar" aria-label={`Прогресс цели «${goal.title}»`} aria-valuemin={0} aria-valuemax={Math.max(goal.total, 1)} aria-valuenow={goal.done} aria-valuetext={`${goal.done} из ${goal.total}`} className={`flex gap-1 overflow-hidden rounded-full ${compact ? 'h-1.5' : 'h-2'}`}>
        {goal.parts.length ? goal.parts.map(part => <span key={part._id} title={`${part.title}${part.cancelled ? ' · отменена' : part.completed ? ' · выполнена' : ''}`} className={`min-w-0 flex-1 rounded-full ${part.completed && !part.cancelled ? 'bg-orange-400' : 'bg-[#E5E9F0]'}`} />) : <span className="w-full rounded-full bg-[#E5E9F0]" />}
      </div>
      {!compact && <p className="mt-2 text-xs text-[#7C8AA0]">{goal.total ? `Выполнено ${goal.done} из ${goal.total} частей` : 'Добавь первую часть цели в расписание'}</p>}
    </div>
  );
}

export default function GoalsDialog({ goals, today, busy, onClose, onCreate, onEdit, onAddPart, onToggle, onRestore }) {
  return (
    <PlanDialog title="Цели недели" onClose={onClose} busy={busy} wide>
      <div className="mb-5 flex items-center justify-between gap-4">
        <p className="max-w-sm text-sm leading-6 text-[#64748B]">Большие задачи недели. Распредели их части по дням и двигайся к результату.</p>
        <button type="button" onClick={onCreate} disabled={busy} className="shrink-0 cursor-pointer rounded-xl bg-orange-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-orange-600 disabled:opacity-40">＋ Цель</button>
      </div>
      {!goals.length && <div className="rounded-2xl border border-dashed border-orange-200 bg-orange-50/50 px-6 py-10 text-center"><p className="font-bold">Что хочешь успеть за неделю?</p><p className="mt-3 text-sm leading-6 text-[#7C8AA0]">Создай цель, а затем добавь несколько небольших шагов в дни недели.</p></div>}
      <div className="space-y-4">
        {goals.map(goal => <article key={goal._id} className="rounded-2xl border border-[#E5E9F0] p-4">
          <div className="mb-3 flex items-start justify-between gap-3">
            <button type="button" onClick={() => onEdit(goal)} className="min-w-0 cursor-pointer break-words text-left font-extrabold hover:text-orange-600">{goal.title}</button>
            <span className={`shrink-0 rounded-lg px-2 py-1 text-xs font-bold ${goal.completed ? 'bg-green-50 text-green-700' : 'bg-orange-50 text-orange-700'}`}>{goal.done}/{goal.total}</span>
          </div>
          {goal.description && <p className="mb-4 whitespace-pre-wrap break-words text-sm leading-6 text-[#64748B]">{goal.description}</p>}
          <GoalProgress goal={goal} />
          {goal.parts.length > 0 && <ul className="mt-4 space-y-3">
            {goal.parts.map(part => <li key={part._id} className="flex items-start gap-2 text-sm">
              <input type="checkbox" checked={part.completed && !part.cancelled} disabled={busy || part.cancelled || part.day > today || (part.inactive && !part.completed)} onChange={() => onToggle(part)} aria-label={`${part.completed ? 'Отменить выполнение' : 'Выполнить'} «${part.title}»`} className="mt-1 h-4 w-4 shrink-0 cursor-pointer accent-orange-500 disabled:cursor-default" />
              <div className="min-w-0 flex-1">
                <button type="button" onClick={() => onEdit(part)} className={`cursor-pointer break-words text-left hover:text-orange-600 ${part.cancelled ? 'text-[#94A3B8] line-through' : ''}`}>{part.title}</button>
                <p className="mt-1 text-xs text-[#94A3B8]">{part.day.slice(8)}.{part.day.slice(5, 7)}{part.time && ` · ${part.time}`}{part.cancelled ? ' · отменена' : part.inactive && !part.completed ? ' · срок истёк' : ''}</p>
              </div>
              {part.cancelled && <button type="button" disabled={busy} onClick={() => onRestore(part)} className="cursor-pointer text-xs font-semibold text-orange-600 hover:underline disabled:opacity-40">Вернуть</button>}
            </li>)}
          </ul>}
          <button type="button" disabled={busy} onClick={() => onAddPart(goal)} className="mt-4 cursor-pointer rounded-lg px-2 py-1.5 text-sm font-semibold text-orange-600 hover:bg-orange-50 disabled:opacity-40">＋ Добавить часть</button>
        </article>)}
      </div>
    </PlanDialog>
  );
}
