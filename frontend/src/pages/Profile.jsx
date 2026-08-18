import { profile } from "../services/apiService/profile";
import { AVATAR_ASSETS } from "../data/data";

import { useState, useEffect } from "react";

import Container from "../components/Container";
import ProfileTabs from "../components/ProfileTabs";
import Attribute from "../components/Attribute";


export default function Profile() {
  const [activeTab, setActiveTab] = useState("info");
  const [data, setData] = useState({});
  const [handleSave, setHandleSave] = useState(<></>)

  useEffect(() => {
    const setCurrentData = (data) => {
      setData(data);
    }
    profile(setCurrentData);
  }, []);

  return (
    <Container>
      <div className="grid mt-12 w-[900px] mx-auto">

        <ProfileTabs active={activeTab} onChange={setActiveTab} />

        <div className="container relative p-6 px-8  text-left mx-auto rounded-b-2xl rounded bg-[#F9FAFE] shadow border- border-[#E5E9F0]">


          {activeTab === "info" && (
            <div>
              <div className="w-[100px] h-[100px] absolute right-6">
                <img src={AVATAR_ASSETS[data.avatar]} className="rounded-full" />
              </div>
              <div className="space-y-2">
                <Attribute title="Имя:">{data.name}</Attribute>
                <Attribute title="Роль:">{data.role}</Attribute>
                <Attribute title="Уровень:">{data.level}</Attribute>
                <Attribute title="Опыт:">{data.xp}</Attribute>
                <Attribute title="Spoints:">{data.Spoints}</Attribute>
                <Attribute title="Серия дней:">{data.days_streak}</Attribute>
                <Attribute title="Множитель опыта:">{data.mul}</Attribute>
                <Attribute title="Процент скидки:">{data.sale_shop}</Attribute>
                <Attribute title="Выполненные простые задания:">{data.complete_simple_tasks}</Attribute>
                <Attribute title="Выполненные обычные задания:">{data.complete_common_tasks}</Attribute>
                <Attribute title="Выполненные трудные задания:">{data.complete_hard_tasks}</Attribute>
                <Attribute title="Выполненные сложные задания:">{data.complete_expert_tasks}</Attribute>
                <Attribute title="Выполненные хардкорные задания:">{data.complete_hardcore_tasks}</Attribute>
              </div>
            </div>
          )}

        {activeTab === "avatar" && (
          <div className="flex gap-8 items-center">
            {Object.entries(AVATAR_ASSETS).map(([key, src]) => (
              <img
                key={key}
                src={src}
                onClick={() => onSelectAvatar(key)}
                className={`w-20 h-20 rounded-full cursor-pointer border-4 ${
                  data.avatar === key ? "border-[#4A6CF7]" : "border-transparent"
                }`}
              />
            ))}
            <span className="text-lg font-bold">Текущий аватар</span>
          </div>
        )}

        {activeTab == "notice" && (
          <div>

          </div>
        )
        }

        {activeTab === "edit" && (
          <form className="space-y-3" onSubmit={handleSave}>
            <input
              className="w-full p-2 rounded-lg border border-[#E5E9F0] bg-white"
              defaultValue={data.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Имя"
            />
            {/* остальные редактируемые поля */}
            <button
              type="submit"
              className="px-4 py-2 rounded-lg bg-[#4A6CF7] text-white"
            >
              Сохранить
            </button>
          </form>
        )}

        </div>
      </div>
    </Container>
  );
}
