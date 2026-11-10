import { NavLink } from "react-router-dom";

const TABS = [
  { to: ".", label: "Информация" },
  { to: "avatars", label: "Аватар" },
  { to: "notifications", label: "Уведомления" },
  { to: "edit", label: "Изменить данные" },
];

export default function ProfileTabs() {
  return (
    <nav aria-label="Разделы профиля" className="flex flex-wrap gap-2 justify-center mb-4 rounded-t-3xl px-3 py-2 bg-[#F1F3FA] shadow border border-[#D5DAE5] sm:px-8">
      {TABS.map((tab) => (
        <NavLink
          key={tab.to}
          to={tab.to}
          end
          className={({ isActive }) => `inline-flex h-8 items-center rounded-full border px-5 text-sm font-medium shadow transition-colors ${
            isActive
              ? "bg-[#4A6CF7] text-white border-[#3A5AE0] hover:bg-[#3A5AE0]"
              : "bg-[#E5E9F5] text-[#5B6478] border-[#D5DAE5] hover:bg-[#D5DAE8]"
          }`}
        >
          {tab.label}
        </NavLink>
      ))}
    </nav>
  );
}
