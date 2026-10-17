import { useEffect, useId, useRef } from 'react';

export default function PlanDialog({ title, children, onClose, busy = false, wide = false }) {
  const dialogRef = useRef(null);
  const titleId = useId();

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
      aria-busy={busy}
      onCancel={event => { event.preventDefault(); if (!busy) onClose(); }}
      onMouseDown={event => { if (!busy && event.target === event.currentTarget) onClose(); }}
      className={`fixed inset-0 m-auto max-h-[calc(100dvh-2rem)] w-[calc(100%-2rem)] ${wide ? 'max-w-2xl' : 'max-w-lg'} overflow-y-auto rounded-2xl border border-[#E5E9F0] bg-white p-0 text-[#1E293B] shadow-2xl backdrop:bg-[#1E293B]/40`}
    >
      <div className="flex items-start justify-between gap-4 border-b border-[#E5E9F0] px-6 py-5">
        <h2 id={titleId} className="text-xl font-extrabold">{title}</h2>
        <button type="button" aria-label="Закрыть окно" disabled={busy} onClick={onClose} className="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-lg text-xl text-[#7C8AA0] hover:bg-[#F2F4F7] focus-visible:outline-2 focus-visible:outline-orange-400 disabled:opacity-40">×</button>
      </div>
      <div className="p-6">{children}</div>
    </dialog>
  );
}
