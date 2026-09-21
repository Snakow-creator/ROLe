import { useState } from "react";

const TABS = [
  { key: "info", label: "Информация" },
  { key: "avatar", label: "Аватар" },
  { key: "notice", label: "Уведомления" },
  { key: "edit", label: "Изменить данные" },
];

export default function ProfileTabs({ active, onChange }) {
  return (
    <div className="flex gap-2 justify-center mb-4 space-x-4 rounded-t-3xl px-8 py-2 bg-[#F1F3FA] shadow border border-[#D5DAE5] h-full">
      {TABS.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onChange(tab.key)}
          className={`px-5 py-2 rounded-full text-sm font-medium transition-colors my-auto cursor-pointer ${
            active === tab.key
              ? "bg-[#4A6CF7] text-white shadow border border-[#3A5AE0] hover:bg-[#3A5AE0] h-8"
              : "bg-[#E5E9F5] text-[#5B6478] shadow border border-[#D5DAE5] hover:bg-[#D5DAE8] h-8"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
