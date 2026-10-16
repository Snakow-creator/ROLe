import { useEffect, useId, useRef } from 'react';

export default function DeleteBoardDialog({ board, onCancel, onConfirm, isDeleting = false, error = '' }) {
  const dialogRef = useRef(null);
  const titleId = useId();
  const descriptionId = useId();

  useEffect(() => {
    const dialog = dialogRef.current;
    const trigger = document.activeElement;
    dialog.showModal();
    return () => {
      dialog.close();
      if (trigger instanceof HTMLElement && trigger.isConnected) trigger.focus();
    };
  }, []);

  return (
    <dialog
      ref={dialogRef}
      aria-labelledby={titleId}
      aria-describedby={descriptionId}
      onCancel={event => { event.preventDefault(); if (!isDeleting) onCancel(); }}
      onMouseDown={event => { if (!isDeleting && event.target === event.currentTarget) onCancel(); }}
      aria-busy={isDeleting}
      className="fixed inset-0 m-auto w-[calc(100%-2rem)] max-w-md rounded-2xl border border-[#E5E9F0] bg-white p-0 text-[#1E293B] shadow-2xl backdrop:bg-[#1E293B]/35"
    >
      <div className="p-6">
        <div aria-hidden="true" className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-red-50 text-red-600">
          <TrashIcon className="h-6 w-6" />
        </div>
        <h2 id={titleId} className="text-xl font-extrabold">Удалить доску?</h2>
        <div id={descriptionId} className="mt-3 space-y-3 text-sm leading-6 text-[#64748B]">
          <p>Доска <strong className="break-words text-[#1E293B]">«{board.title}»</strong> и все её квесты будут удалены.</p>
          <p>Будут удалены и выполненные, просроченные и запланированные квесты. Начисленные Spoints и XP сохранятся.</p>
          <p className="font-semibold text-red-600">Это действие нельзя отменить.</p>
        </div>
        {error && <p role="alert" className="mt-4 text-sm leading-6 text-red-600">{error}</p>}
        <div className="mt-6 flex justify-end gap-3">
          <button autoFocus type="button" disabled={isDeleting} onClick={onCancel} className="cursor-pointer rounded-lg border border-[#E5E9F0] px-4 py-2.5 text-sm font-semibold hover:bg-[#F2F4F7] focus-visible:outline-2 focus-visible:outline-green-500 disabled:cursor-not-allowed disabled:opacity-60">Оставить доску</button>
          <button type="button" disabled={isDeleting} onClick={onConfirm} className="cursor-pointer rounded-lg bg-red-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-red-700 focus-visible:outline-2 focus-visible:outline-red-500 focus-visible:outline-offset-2 disabled:cursor-not-allowed disabled:opacity-60">{isDeleting ? 'Удаляем…' : 'Удалить доску'}</button>
        </div>
      </div>
    </dialog>
  );
}

export function TrashIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M3 6h18M9 6V4h6v2M5 6l1 14h12l1-14M10 10v6M14 10v6" />
    </svg>
  );
}
