const dayPlural = new Intl.PluralRules('ru');
const dayWords = { one: 'день', few: 'дня', many: 'дней', other: 'дня' };

export default function BoardInfo({ points = 0, xp = 0, days = null }) {
  const duration = days == null ? 'Без срока'
    : days === 1 ? 'До 12:00 следующего дня · МСК'
    : `${days} ${dayWords[dayPlural.select(days)]}`;

  return (
    <p
      className="ml-4 mt-1 text-xs font-normal leading-5 text-[#7C8AA0]"
      title="Базовая награда за один квест и срок его выполнения"
    >
      {points} Spoints · {xp} XP · {duration}
    </p>
  );
}
