import { useOutletContext } from "react-router-dom";

import Attribute from "../../components/Attribute";
import { avatarUrl } from "../../data/data";

export default function ProfileInfo() {
  const { data } = useOutletContext();

  return (
    <div>
      <div className="size-20 sm:size-[100px] absolute right-6">
        <img src={avatarUrl(data.avatar)} alt="Аватар профиля" className="size-full rounded-full object-cover" />
      </div>
      <div className="space-y-2 pr-24 sm:pr-28">
        <Attribute title="Имя:">{data.name}</Attribute>
        <Attribute title="Роль:">{data.role}</Attribute>
        <Attribute title="Уровень:">{data.level}</Attribute>
        <Attribute title="Опыт:">{data.xp}</Attribute>
        <Attribute title="Spoints:">{data.Spoints}</Attribute>
        <Attribute title="Серия дней:">{data.days_streak}</Attribute>
        <Attribute title="Множитель опыта:">{data.mul}</Attribute>
        <Attribute title="Процент скидки:">{data.sale_shop}</Attribute>
        {data.boards?.map(board => (
          <Attribute key={board._id} title={`Выполненные квесты (${board.title}):`}>
            {board.completed_tasks}
          </Attribute>
        ))}
      </div>
    </div>
  );
}
