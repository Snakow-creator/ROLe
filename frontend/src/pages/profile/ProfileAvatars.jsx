import { useOutletContext } from "react-router-dom";

import { avatarUrl } from "../../data/data";

export default function ProfileAvatars() {
  const { data, avatarPicker } = useOutletContext();
  const { selectedAvatar, chooseAvatar, saveAvatar, savingAvatar, saveError } = avatarPicker;

  return (
    <section aria-labelledby="avatar-title">
      <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
        <h2 id="avatar-title" className="text-lg font-bold">Коллекция аватаров</h2>
        <button
          type="button"
          onClick={saveAvatar}
          disabled={savingAvatar || !selectedAvatar || selectedAvatar === data.avatar}
          className="rounded-lg bg-[#4A6CF7] px-4 py-2 text-white enabled:cursor-pointer disabled:opacity-50"
        >
          {savingAvatar ? "Сохраняем…" : "Сохранить аватар"}
        </button>
      </div>
      {saveError && <p className="mb-4 text-sm text-red-700" role="alert">{saveError}</p>}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        {data.avatars.map(avatar => {
          const selected = avatar.id === (selectedAvatar ?? data.avatar);
          return (
            <button
              key={avatar.id}
              type="button"
              disabled={!avatar.available || savingAvatar}
              aria-pressed={selected}
              onClick={() => chooseAvatar(avatar.id)}
              className={`flex min-w-0 flex-col items-center gap-2 rounded-xl border-2 p-3 text-center text-sm ${
                selected ? "border-[#4A6CF7]" : "border-[#E5E9F0]"
              } ${avatar.available ? "bg-white enabled:cursor-pointer" : "bg-slate-50 text-slate-600"}`}
            >
              <img
                src={avatarUrl(avatar.id)}
                alt=""
                loading="lazy"
                className={`size-16 rounded-full object-cover sm:size-20 ${avatar.available ? "" : "opacity-45"}`}
              />
              <span className="font-medium">{avatar.label}</span>
              {avatar.id === data.avatar && <span className="text-blue-700">Текущий</span>}
              {!avatar.available && <span className="text-xs">{avatar.unlock_hint}</span>}
            </button>
          );
        })}
      </div>
    </section>
  );
}
