import { useRef, useState } from "react";

import Button from "../Button";
import Textarea from "../Textarea";
import { createBoard } from "../../services/apiService/boards";

const inputClassName = "bg-white appearance-none border border-[#F1F1F1] shadow w-full hover:outline-2 hover:outline-blue-400 focus-visible:outline-2 focus-visible:outline-blue-400 rounded-md text-left p-1 px-2";

export default function FormCreateBoard({ onCancel, onCreated }) {
  const [formData, setFormData] = useState({
    title: "",
    award_points: "0",
    award_xp: "0",
    is_weekly: false,
    task_expire_days: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");
  const submittingRef = useRef(false);

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    setFormData(current => ({
      ...current,
      [name]: type === "checkbox" ? checked : value,
    }));
    setError("");
  };

  const submitBoard = async (event) => {
    event.preventDefault();
    if (submittingRef.current) return;

    const title = formData.title.trim();
    if (!title || title.length > 100) {
      setError("Введите название доски от 1 до 100 символов.");
      return;
    }

    const points = Number(formData.award_points);
    const xp = Number(formData.award_xp);
    if (
      formData.award_points === "" || formData.award_xp === "" ||
      !Number.isSafeInteger(points) || points < 0 ||
      !Number.isSafeInteger(xp) || xp < 0
    ) {
      setError("Очки и опыт должны быть целыми числами от 0.");
      return;
    }

    const days = formData.task_expire_days === "" ? null : Number(formData.task_expire_days);
    if (days !== null && (!Number.isSafeInteger(days) || days < 1 || days > 36500)) {
      setError("Укажите от 1 до 36500 дней или оставьте срок пустым.");
      return;
    }

    submittingRef.current = true;
    setIsSubmitting(true);
    setError("");
    let board;
    try {
      board = await createBoard({
        title,
        award_points: points,
        award_xp: xp,
        is_weekly: formData.is_weekly,
        task_expire_days: days,
      });
    } catch (requestError) {
      const status = requestError.response?.status;
      setError(status === 401
        ? "Войдите в аккаунт, чтобы создать доску."
        : status === 422
          ? "Проверьте название, награды и срок выполнения."
          : "Не удалось создать доску. Попробуйте ещё раз.");
      return;
    } finally {
      submittingRef.current = false;
      setIsSubmitting(false);
    }

    onCreated(board);
  };

  const handleKeyDown = (event) => {
    if (event.nativeEvent.isComposing) return;
    if (event.key === "Escape" && !submittingRef.current) {
      event.preventDefault();
      onCancel();
    }
    if (event.target.tagName === "TEXTAREA" && event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (!event.repeat) event.currentTarget.requestSubmit();
    }
  };

  return (
    <form
      onSubmit={submitBoard}
      onKeyDown={handleKeyDown}
      noValidate
      aria-label="Создание доски"
      className="bg-[#F9FAFE] flex-shrink-0 rounded-2xl py-3 px-2 w-[275px] 2xl:w-[320px] shadow border border-[#E5E9F0]"
    >
      <h2 className="ml-4 font-extrabold">Новая доска</h2>

      <fieldset disabled={isSubmitting} className="mt-2 space-y-3 disabled:opacity-60">
        <label className="block text-sm font-medium text-[#334155]">
          Название доски
          <Textarea
            className={`${inputClassName} mt-1 min-h-16 resize-none font-normal`}
            placeholder="Введите название доски"
            maxLength="100"
            name="title"
            focus={true}
            value={formData.title}
            onChange={handleChange}
          />
        </label>

        <div className="grid grid-cols-2 gap-2">
          <label className="block text-sm font-medium text-[#334155]">
            Очки за квест
            <input className={`${inputClassName} mt-1 font-normal`} type="number" name="award_points" min="0" step="1" required value={formData.award_points} onChange={handleChange} />
          </label>
          <label className="block text-sm font-medium text-[#334155]">
            Опыт за квест
            <input className={`${inputClassName} mt-1 font-normal`} type="number" name="award_xp" min="0" step="1" required value={formData.award_xp} onChange={handleChange} />
          </label>
        </div>

        <label className="flex items-center gap-2 text-sm font-medium text-[#334155] cursor-pointer">
          <input type="checkbox" name="is_weekly" checked={formData.is_weekly} onChange={handleChange} className="h-4 w-4 accent-[#3B82F6]" />
          Недельная доска
        </label>
        <p className="text-xs text-[#7C8AA0]">Недельный бонус за завершение всех активных квестов доски.</p>

        <label className="block text-sm font-medium text-[#334155]">
          Дни на выполнение квеста
          <input className={`${inputClassName} mt-1 font-normal`} type="number" name="task_expire_days" min="1" max="36500" step="1" placeholder="Без ограничения" value={formData.task_expire_days} onChange={handleChange} />
        </label>
        <p className="text-xs text-[#7C8AA0]">Оставьте поле пустым, если квесты не должны истекать.</p>
      </fieldset>

      {error && <p role="alert" className="mt-3 text-sm text-red-600">{error}</p>}

      <div className="mt-3 flex items-center justify-between">
        <Button type="submit" disabled={isSubmitting} className="ml-2 mt-0 text-sm p-1 px-2">
          {isSubmitting ? "Добавляем…" : "Добавить"}
        </Button>
        <button type="button" disabled={isSubmitting} onClick={onCancel} aria-label="Отменить создание доски" className="text-2xl text-[#7C8AA0] mr-1 w-6 h-8 cursor-pointer hover:bg-[#EEF2F7] active:bg-[#E5E9F0] hover:shadow active:shadow rounded-md disabled:cursor-not-allowed disabled:opacity-60">
          ╳
        </button>
      </div>
    </form>
  );
}
