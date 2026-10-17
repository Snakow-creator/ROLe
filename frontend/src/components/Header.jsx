import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';

import { logout, getAuth } from '../services/apiService/auth';
import { getAvatar } from '../services/apiService/users';
import { AVATAR_ASSETS } from '../data/data';
import LinkHeader from './LinkHeader';

export default function Header() {
  const [bar, setBar] = useState(<></>);
  const [navigation, setNavigation] = useState(<></>);
  const [auth, setAuth] = useState(null);
  const [avatar, setAvatar] = useState(null);

  const logoutUser = async () => {
    const setAuthFalse = () => {
      setAuth(false);
    }

    await logout({setAuthFalse});
  }

  const handleNavigation = () => {
    // if auth is true
    setNavigation(auth &&
      // navigation, near right with logo
      <nav aria-label="Основная навигация" className="flex min-w-0 items-center gap-1 overflow-x-auto sm:gap-4 lg:gap-8">
        <LinkHeader to="/quests" className="shrink-0 whitespace-nowrap text-xs sm:text-sm lg:text-lg">мои квесты</LinkHeader>
        <LinkHeader to="/plan" className="shrink-0 whitespace-nowrap text-xs sm:text-sm lg:text-lg">план недели</LinkHeader>
        <LinkHeader to="/items" className="shrink-0 whitespace-nowrap text-xs sm:text-sm lg:text-lg">магазин</LinkHeader>
      </nav>
    )
  }



  const handleAuth = () => {
    if (auth) {
      setBar(
        <>
          <Link to="/profile" className='w-10 h-10 inline-block border overflow-hidden rounded-full'>
            <img src={avatar} className="w-full h-full object-cover"/>
          </Link>
          <button className='cursor-pointer w-[30px] h-[30px]' onClick={logoutUser}>
            <img src="/header/logout.svg"/>
          </button>
        </>
      )
    } else {
      setBar(
        <>
          <LinkHeader to="/register">регистрация</LinkHeader>
          <LinkHeader to="/login">войти</LinkHeader>
        </>
      )
    }
  }
  useEffect(() => {
    const checkAuth = async () => {
      const res = await getAuth();
      setAuth(res.auth);
    }

    const checkAvatar = async () => {
      const onUpdateAvatar = avatarId => {
        setAvatar(AVATAR_ASSETS[avatarId]);
      }
      await getAvatar(onUpdateAvatar);
    }

    checkAvatar();
    checkAuth();
  }, []);

  useEffect(() => {
    handleAuth();
    handleNavigation();
  }, [auth]);

  return (
    <header className="fixed top-0 left-0 w-full bg-[#FAFBFF] z-50">
      <div className="flex items-center justify-between gap-3 px-3 py-2 md:px-4">
        {/* logo */}
        <div className="flex min-w-0 items-center gap-3 sm:gap-8">
          <Link to="/" className="shrink-0">
            <h1 className="font-acme text-2xl md:text-3xl"><span className="sm:hidden">ROLe</span><span className="hidden sm:inline">Realms of Life</span></h1>
          </Link>
          { navigation }
        </div>

        <div className="flex shrink-0 items-center gap-3 sm:gap-8">
          { bar }
        </div>
      </div>
      <hr className="shadow-2xl"/>
    </header>
  );
}
