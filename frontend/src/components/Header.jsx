import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';

import { logout, getAuth } from '../services/apiService/auth';
import { getProfile } from '../services/apiService/profile';
import { avatarUrl } from '../data/data';
import LinkHeader from './LinkHeader';

const DEFAULT_AVATAR = avatarUrl();

export default function Header() {
  const [auth, setAuth] = useState(null);
  const [avatar, setAvatar] = useState(DEFAULT_AVATAR);

  const logoutUser = async () => {
    await logout({ setAuthFalse: () => {
      setAuth(false);
      setAvatar(DEFAULT_AVATAR);
    } });
  };

  useEffect(() => {
    let active = true;
    let revision = 0;
    const checkProfile = async () => {
      const current = ++revision;
      const isCurrent = () => active && current === revision;
      try {
        const res = await getAuth();
        if (!isCurrent()) return;
        setAuth(Boolean(res?.auth));
        setAvatar(DEFAULT_AVATAR);

        if (res?.auth) {
          const profile = await getProfile();
          if (isCurrent()) setAvatar(avatarUrl(profile.avatar));
        }
      } catch (error) {
        console.error('Не удалось загрузить профиль в шапке:', error);
      }
    };

    checkProfile();
    window.addEventListener('auth-change', checkProfile);
    window.addEventListener('avatar-change', checkProfile);
    window.addEventListener('storage', checkProfile);
    return () => {
      active = false;
      window.removeEventListener('auth-change', checkProfile);
      window.removeEventListener('avatar-change', checkProfile);
      window.removeEventListener('storage', checkProfile);
    };
  }, []);

  return (
    <header className="fixed top-0 left-0 w-full bg-[#FAFBFF] z-50">
      <div className="flex items-center justify-between gap-3 px-3 py-2 md:px-4">
        <div className="flex min-w-0 items-center gap-3 sm:gap-8">
          <Link to="/" className="shrink-0">
            <h1 className="font-acme text-2xl md:text-3xl"><span className="sm:hidden">ROLe</span><span className="hidden sm:inline">Realms of Life</span></h1>
          </Link>
          {auth && (
            <nav aria-label="Основная навигация" className="flex min-w-0 items-center gap-1 overflow-x-auto sm:gap-4 lg:gap-8">
              <LinkHeader to="/quests" className="shrink-0 whitespace-nowrap text-xs sm:text-sm lg:text-lg">мои квесты</LinkHeader>
              <LinkHeader to="/plan" className="shrink-0 whitespace-nowrap text-xs sm:text-sm lg:text-lg">план недели</LinkHeader>
              <LinkHeader to="/items" className="shrink-0 whitespace-nowrap text-xs sm:text-sm lg:text-lg">магазин</LinkHeader>
            </nav>
          )}
        </div>

        <div className="flex shrink-0 items-center gap-3 sm:gap-8">
          {auth ? (
            <>
              <Link to="/profile" aria-label="Профиль" className="inline-block h-10 w-10 shrink-0 overflow-hidden rounded-full border">
                <img key={avatar} src={avatar} alt="Аватар профиля" className="h-full w-full object-cover" onError={event => {
                  if (avatar !== DEFAULT_AVATAR) setAvatar(DEFAULT_AVATAR);
                  else event.currentTarget.hidden = true;
                }} />
              </Link>
              <button type="button" aria-label="Выйти из аккаунта" className="h-[30px] w-[30px] shrink-0 cursor-pointer" onClick={logoutUser}>
                <img src="/header/logout.svg" alt="" />
              </button>
            </>
          ) : auth === false ? (
            <>
              <LinkHeader to="/register">регистрация</LinkHeader>
              <LinkHeader to="/login">войти</LinkHeader>
            </>
          ) : null}
        </div>
      </div>
      <hr className="shadow-2xl"/>
    </header>
  );
}
