import Container from "../components/Container";
import { profile } from "../services/apiService/profile";
import { useState, useEffect } from "react";


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
      <h1 className="text-3xl font-extrabold">Профиль</h1>
      <div>
        <p>Имя: <b>{data.name}</b></p>
        <p>Роль: <b>{data.role}</b></p>
        <p>Уровень: <b>{data.level}</b></p>
        <p>Опыт: <b>{data.xp}</b></p>
        <p>Spoints: <b>{data.Spoints}</b></p>
        <p>Серия дней: <b>{data.days_streak}</b></p>
        <p>Множитель опыта: <b>{data.mul}</b></p>
        <p>Процент скидки: <b>{data.sale_shop}</b></p>
        <p>Выполненные простые задания: <b>{data.complete_simple_tasks}</b></p>
        <p>Выполненные обычные задания: <b>{data.complete_common_tasks}</b></p>
        <p>Выполненные трудные задания: <b>{data.complete_hard_tasks}</b></p>
        <p>Выполненные сложные задания: <b>{data.complete_expert_tasks}</b></p>
        <p>Выполненные хардкорные задания: <b>{data.complete_hardcore_tasks}</b></p>
      </div>
    </Container>
  );
}
