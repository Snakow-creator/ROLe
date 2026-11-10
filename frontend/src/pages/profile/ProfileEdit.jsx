import { useOutletContext } from "react-router-dom";

export default function ProfileEdit() {
  const { data } = useOutletContext();

  return (
    <section aria-labelledby="edit-title" className="space-y-3">
      <h2 id="edit-title" className="text-lg font-bold">Изменить данные</h2>
      <label htmlFor="profile-name" className="block text-sm font-medium">Имя</label>
      <input
        id="profile-name"
        className="w-full rounded-lg border border-[#E5E9F0] bg-white p-2"
        value={data.name}
        readOnly
      />
      <p className="text-sm text-slate-600">Сохранение изменений пока недоступно.</p>
    </section>
  );
}
