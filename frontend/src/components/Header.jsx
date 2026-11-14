import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';

import { logout, getAuth } from '../services/apiService/auth';
import { BALANCE_CHANGE_EVENT, getProfile } from '../services/apiService/profile';
import { getAccessToken } from '../hooks/getTokens';
import BASE_URL from '../data/config';
import { avatarUrl } from '../data/data';
import LinkHeader from './LinkHeader';

const DEFAULT_AVATAR = avatarUrl();
const CURRENCIES = [
  ['Qpoints', 'qpoints.svg'],
  ['Spoints', 'spoints.svg'],
  ['Tpoints', 'tpoints.svg'],
];
const balanceFormat = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 2 });

function HeaderBalances({ profile }) {
  return (
    <ul aria-label="Баланс очков" className="flex min-w-0 items-center gap-2 overflow-x-auto sm:gap-3">
      {CURRENCIES.map(([currency, icon]) => {
        const value = profile?.[currency];
        const amount = Number.isFinite(value) ? balanceFormat.format(value) : '…';
        return (
          <li key={currency} className="flex shrink-0 items-center gap-0.5 rounded-full border border-[#E5E9F0] bg-white px-1.5 py-1 text-xs font-bold tabular-nums sm:gap-1 sm:px-2 sm:text-sm">
            <img src={`${BASE_URL}${icon}`} className="size-4 shrink-0 sm:size-5" alt="" />
            <span className="sr-only">{currency}{' '}</span>
            <span className="whitespace-nowrap">{amount}</span>
          </li>
        );
      })}
    </ul>
  );
}

export default function Header() {
  const [auth, setAuth] = useState(null);
  const [profile, setProfile] = useState(null);
  const [failedAvatar, setFailedAvatar] = useState(null);
  const profileAvatar = avatarUrl(profile?.avatar);
  const avatar = profileAvatar === failedAvatar ? DEFAULT_AVATAR : profileAvatar;

  const logoutUser = async () => {
    await logout({ setAuthFalse: () => {
      setAuth(false);
      setProfile(null);
    } });
  };

  useEffect(() => {
    let active = true;
    let authRevision = 0;
    let profileRequest;

    const refreshProfile = async () => {
      profileRequest?.abort();
      const request = new AbortController();
      profileRequest = request;
      try {
        const data = await getProfile(request.signal);
        if (!request.signal.aborted) {
          setProfile(data);
          setFailedAvatar(null);
        }
      } catch (error) {
        if (!request.signal.aborted) console.error('Не удалось загрузить профиль в шапке:', error);
      }
    };

    const checkAuth = async () => {
      const current = ++authRevision;
      profileRequest?.abort();
      setProfile(null);
      const res = await getAuth();
      if (!active || current !== authRevision) return;
      setAuth(Boolean(res?.auth));
      if (res?.auth) await refreshProfile();
    };

    const onProfileChange = () => {
      if (getAccessToken()) refreshProfile();
    };

    const onStorage = (event) => {
      if (event.key === 'access_token' || event.key === null) checkAuth();
    };

    checkAuth();
    window.addEventListener('auth-change', checkAuth);
    window.addEventListener('avatar-change', onProfileChange);
    window.addEventListener(BALANCE_CHANGE_EVENT, onProfileChange);
    window.addEventListener('storage', onStorage);
    return () => {
      active = false;
      profileRequest?.abort();
      window.removeEventListener('auth-change', checkAuth);
      window.removeEventListener('avatar-change', onProfileChange);
      window.removeEventListener(BALANCE_CHANGE_EVENT, onProfileChange);
      window.removeEventListener('storage', onStorage);
    };
  }, []);

  return (
    <header className="sticky top-0 z-50 bg-[#FAFBFF]">
      <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-2 px-3 py-2 md:gap-x-6 md:px-4">
        <div className={`flex min-w-0 items-center gap-3 md:flex-1 md:gap-6 ${auth ? 'w-full md:w-auto' : ''}`}>
          <Link to="/" className="shrink-0">
            <h1 className="font-acme text-2xl md:text-3xl"><span className="lg:hidden">ROLe</span><span className="hidden lg:inline">Realms of Life</span></h1>
          </Link>
          {auth && (
            <nav aria-label="Основная навигация" className="flex min-w-0 items-center gap-1 overflow-x-auto sm:gap-4 lg:gap-8">
              <LinkHeader to="/quests" className="shrink-0 whitespace-nowrap text-xs sm:text-sm lg:text-lg">мои квесты</LinkHeader>
              <LinkHeader to="/plan" className="shrink-0 whitespace-nowrap text-xs sm:text-sm lg:text-lg">план недели</LinkHeader>
              <LinkHeader to="/items" className="shrink-0 whitespace-nowrap text-xs sm:text-sm lg:text-lg">магазин</LinkHeader>
            </nav>
          )}
        </div>

        <div className="flex min-w-0 flex-1 items-center justify-end gap-3 sm:gap-5 md:flex-none md:max-w-[55%] lg:gap-7">
          {auth ? (
            <>
              <HeaderBalances profile={profile} />
              <Link to="/profile" aria-label="Профиль" className="inline-block h-10 w-10 shrink-0 overflow-hidden rounded-full border">
                <img key={avatar} src={avatar} alt="Аватар профиля" className="h-full w-full object-cover" onError={event => {
                  if (avatar !== DEFAULT_AVATAR) setFailedAvatar(avatar);
                  else event.currentTarget.hidden = true;
                }} />
              </Link>
              <button
                type="button"
                aria-label="Выйти из аккаунта"
                className="grid size-[30px] shrink-0 cursor-pointer place-items-center rounded-md transition-colors hover:bg-[#E9EDF3] active:bg-[#E5E9F0] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-500"
                onClick={logoutUser}
              >
                <img src={`${BASE_URL}header/logout.svg`} width="20" height="20" alt="" />
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
