import { useEffect, useState } from "react";
import { Outlet } from "react-router-dom";

import Container from "../components/Container";
import ProfileTabs from "../components/ProfileTabs";
import { getProfile } from "../services/apiService/profile";
import { selectAvatar } from "../services/apiService/users";

export default function Profile() {
  const [data, setData] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [selectedAvatar, setSelectedAvatar] = useState(null);
  const [savingAvatar, setSavingAvatar] = useState(false);
  const [saveError, setSaveError] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    getProfile(controller.signal).then(setData).catch(() => {
      if (!controller.signal.aborted) setLoadError("Не удалось загрузить профиль.");
    });
    return () => controller.abort();
  }, []);

  const chooseAvatar = (avatarId) => {
    setSelectedAvatar(avatarId);
    setSaveError("");
  };

  const saveAvatar = async () => {
    setSavingAvatar(true);
    setSaveError("");
    try {
      const avatar = await selectAvatar(selectedAvatar);
      setData(previous => ({ ...previous, avatar }));
      setSelectedAvatar(null);
      window.dispatchEvent(new Event("avatar-change"));
    } catch {
      setSaveError("Не удалось сохранить аватар. Попробуй ещё раз.");
    } finally {
      setSavingAvatar(false);
    }
  };

  if (!data) {
    return (
      <Container>
        <p className="mt-12 text-center" role={loadError ? "alert" : "status"}>
          {loadError || "Загружаем профиль…"}
        </p>
      </Container>
    );
  }

  return (
    <Container>
      <div className="grid mt-12 w-full max-w-[900px] mx-auto">
        <ProfileTabs />
        <div className="container relative p-6 px-8 text-left mx-auto rounded-b-2xl rounded bg-[#F9FAFE] shadow border-[#E5E9F0]">
          <Outlet context={{
            data,
            avatarPicker: { selectedAvatar, chooseAvatar, saveAvatar, savingAvatar, saveError },
          }} />
        </div>
      </div>
    </Container>
  );
}
