import { Routes, Route } from 'react-router-dom';

import Header from './components/Header';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import Tasks from './pages/Tasks';
import Items from './pages/Items';



export default function App() {
  return (
    <div>
      <Header />

      <main className='pt-[57px]'>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/quests" element={<Tasks />} />
          <Route path="/items" element={<Items />} />
        </Routes>
      </main>
    </div>
  );
}
