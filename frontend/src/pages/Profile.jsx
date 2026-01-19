import { profile } from "../services/apiService/profile";
import { AVATAR_ASSETS } from "../data/data";

import { useState, useEffect } from "react";

import Container from "../components/Container";
import Attribute from "../components/Attribute";


export default function Profile() {
  const [data, setData] = useState({});

  useEffect(() => {
    const setCurrentData = (data) => {
      setData(data);
    }
    profile(setCurrentData);
  }, []);

  return (
    <Container>
      <div className="container relative mt-12 p-6 px-8 w-[900px] text-left mx-auto rounded-2xl bg-[#F9FAFE] shadow border border-[#E5E9F0]">
        <div className="w-[100px] h-[100px] absolute right-6">
          <img src={AVATAR_ASSETS[data.avatar]} className="rounded-full"/>
        </div>
        <div className="space-y-2">
          <Attribute
            title="Имя:">
            {data.name}
          </Attribute>
          <Attribute
            title="Роль:">
            {data.role}
          </Attribute>
          <Attribute
            title="Уровень:">
            {data.level}
          </Attribute>
          <Attribute
            title="Опыт:">
            {data.xp}
          </Attribute>
          <Attribute
            title="Spoints:">
            {data.Spoints}
          </Attribute>
          <Attribute
            title="Серия дней:">
            {data.days_streak}
          </Attribute>
          <Attribute
            title="Множитель опыта:">
            {data.mul}
          </Attribute>
          <Attribute
            title="Процент скидки:">
            {data.sale_shop}
          </Attribute>
          <Attribute
            title="Выполненные простые задания:">
            {data.complete_simple_tasks}
          </Attribute>
          <Attribute
            title="Выполненные обычные задания:">
            {data.complete_common_tasks}
          </Attribute>
          <Attribute
            title="Выполненные трудные задания:">
            {data.complete_hard_tasks}
          </Attribute>
          <Attribute
            title="Выполненные сложные задания:">
            {data.complete_expert_tasks}
          </Attribute>
          <Attribute
            title="Выполненные хардкорные задания:">
            {data.complete_hardcore_tasks}
          </Attribute>
        </div>
      </div>
    </Container>
  );
}
