import { Routes, Route } from 'react-router-dom';

import Header from './components/Header';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Profile from './pages/Profile';
import ProfileInfo from './pages/profile/ProfileInfo';
import ProfileAvatars from './pages/profile/ProfileAvatars';
import ProfileNotifications from './pages/profile/ProfileNotifications';
import ProfileEdit from './pages/profile/ProfileEdit';
import Tasks from './pages/Tasks';
import Items from './pages/Items';
import Plan from './pages/Plan';

import { NotificationProvider } from './context/NotificationContext';



export default function App() {
  return (
    <NotificationProvider>
      <div>
        <Header />

        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/profile" element={<Profile />}>
              <Route index element={<ProfileInfo />} />
              <Route path="avatars" element={<ProfileAvatars />} />
              <Route path="notifications" element={<ProfileNotifications />} />
              <Route path="edit" element={<ProfileEdit />} />
            </Route>
            <Route path="/quests" element={<Tasks />} />
            <Route path="/plan" element={<Plan />} />
            <Route path="/items" element={<Items />} />
          </Routes>
        </main>
      </div>
    </NotificationProvider>
  );
}
