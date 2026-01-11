import { Routes, Route } from 'react-router-dom';

import Header from './components/Header';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import AddTask from './pages/CreateTask';
import Tasks from './pages/Tasks';
import Items from './pages/Items';



export default function App() {
  return (
    <div>
      <Header />

      <main>
        
        <div className='mt-2 lg:w-[70%] md:w-[80%] sm-[90%] mx-auto text-center'>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/profile" element={<Profile />} />
          </Routes>
        </div>

        <Routes>
          <Route path="/add/task" element={<AddTask />} />
          <Route path="/tasks" element={<Tasks />} />
          <Route path="/items" element={<Items />} />
        </Routes>
      </main>
    </div>
  );
}
