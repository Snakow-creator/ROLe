import { Link } from 'react-router-dom';
import { useState, useEffect } from 'react';

import { logout, getAuth } from '../services/apiService/auth';
import LinkHeader from './LinkHeader';

export default function Header() {
  const [bar, setBar] = useState(<></>);
  const [navigation, setNavigation] = useState(<></>);
  const [auth, setAuth] = useState(null);

  const checkAuth = async () => {
    const res = await getAuth();
    setAuth(res.auth);
  }

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
      <nav className="flex items-center space-x-8">
        <LinkHeader to="/quests">мои квесты</LinkHeader>
        <LinkHeader to="/items">магазин</LinkHeader>
      </nav>
    )
  }



  const handleAuth = () => {
    if (auth) {
      setBar(
        <>
          <h3 className="bg-gray-400 border w-10 h-10 rounded-full">
            <Link to="/profile" className='absolute w-10 h-10 rounded-full'></Link>
          </h3>
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
    checkAuth();
  }, []);

  useEffect(() => {
    handleAuth();
    handleNavigation();
  }, [auth]);

  return (
    <header className="bg-[#FAFBFF]">
      <div className="flex items-center justify-between py-2 ml-4">
        {/* logo */}
        <div className="flex items-center space-x-8">
          <Link to="/">
            <h1 className="font-acme text-3xl">Realms of Life</h1>
          </Link>
          { navigation }
        </div>

        <div className="flex items-center space-x-8 mr-8">
          { bar }
        </div>
      </div>
      <hr className="shadow-2xl"/>
    </header>
  );
}
