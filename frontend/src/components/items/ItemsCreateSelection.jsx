// components/items/ItemsCreateSection.jsx
import FormCreateItem from "../forms/FormCreateItem";

// field to create item
export default function ItemsCreateSelection({
  isFormOpen, setIsFormOpen, formRef, onSubmit, onUpdate,
}) {
  if (!isFormOpen) {
    return (
      <button
        className="relative flex items-center space-x-1 bg-[#ffffff] text-[#67748A] cursor-pointer font-bold shadow text-lg rounded-xl px-6 py-3 w-full border border-[#F1F1F1] hover:bg-[#F7F7F7] active:bg-[#F1F1F1]"
        type="button"
        onClick={() => setIsFormOpen(true)}>
        ＋ Добавить услугу
      </button>
    );
  }

  return (
    <div ref={formRef} onClick={(e) => e.target === e.currentTarget && setIsFormOpen(false)}>
      <FormCreateItem onSubmit={onSubmit} onUpdate={onUpdate} />
    </div>
  );
}
