import Container from "../components/Container";
import { Link } from "react-router-dom";
import { useEffect, useState } from "react";
import { getAuth } from "../services/apiService/auth";

export default function Home() {
  const [authenticated, setAuthenticated] = useState(null);

  useEffect(() => {
    let active = true;
    let revision = 0;
    const checkAuth = async () => {
      const current = ++revision;
      const result = await getAuth();
      if (active && current === revision) setAuthenticated(Boolean(result?.auth));
    };

    checkAuth();
    window.addEventListener("auth-change", checkAuth);
    window.addEventListener("storage", checkAuth);
    return () => {
      active = false;
      window.removeEventListener("auth-change", checkAuth);
      window.removeEventListener("storage", checkAuth);
    };
  }, []);

  return (
    <Container>
      <section aria-labelledby="home-title" className="mt-4 rounded-2xl bg-white px-5 py-8 shadow-sm md:mt-10 md:px-10 md:py-10">
        <h1 id="home-title" className="whitespace-nowrap font-acme text-2xl sm:text-3xl">ROLe · Realms Of Life</h1>

        <div className="mx-auto mt-8 x-full space-y-4 text-left text-base leading-relaxed sm:text-lg">
          <p>
            ROLe — больше, чем сервис заметок. Это сервис геймификации твоего
            процесса развития: здесь планы и повседневные дела становятся
            квестами, за которые ты получаешь опыт и награды. Сделай рутину увлекательнее.
          </p>
          <p>
            В основе — твои собственные цели. Учёба, тренировки, работа над
            проектом или домашние дела: добавляй задачи и выбирай для них
            подходящую сложность. Большую цель можно разбить на небольшие
            части и распределить их по дням в плане недели.
          </p>
          <p>
            За выполненные квесты ты получаешь опыт и Spoints. Опыт повышает
            уровень, а Spoints можно потратить в магазине — награды для себя
            ты придумываешь сам. Это может быть вечер за любимой игрой,
            поход в кино или покупка, которую давно откладывал.
          </p>
          <p>
            План недели помогает распределить дела по дням, а статистика —
            посмотреть, сколько уже сделано. Уровень, серия дней и выполненные
            квесты сохраняют историю твоих усилий, даже когда до большой цели
            ещё далеко.
          </p>
          <p>
            Ты сам решаешь, над чем работать и чем себя поощрять. ROLe помогает
            собрать эти планы в одном месте и сделать результат каждого дня
            заметнее.
          </p>
        </div>

        {authenticated !== null && (
          <Link to={authenticated ? "/profile" : "/login"} className="mt-8 inline-block rounded-md border border-[#2563EB] bg-[#3B82F6] px-6 py-2 text-white hover:bg-[#2563EB] active:bg-[#1D4ED8] focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[#2563EB]">
            {authenticated ? "Профиль" : "Войти"}
          </Link>
        )}
      </section>
    </Container>
  );
}
