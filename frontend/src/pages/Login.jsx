import Button from "../components/Button";
import { MessageError } from "../components/Message";
import Container from "../components/Container";

import { login } from "../services/apiService/auth";

import { useState } from "react";


export default function Login() {
  const [showPassword, setShowPassword] = useState(false);
  const [messageError, setMessageError] = useState(<></>);
  const [formData, setFormData] = useState({
    name: "",
    password: ""
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev, [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const changeMessageError = () => {
      setMessageError(
        <MessageError>
          Неверное имя пользователя или пароль
        </MessageError>
      )
    }

    await login({ formData, changeMessageError });
  }

  const handleShowPassword = () => {
    setShowPassword(!showPassword);
  }


  return (
    <Container>
      <div className="container md:w-[50%] mx-auto rounded-2xl md:mt-16 mt-4 py-4 bg-white shadow-sm">

        <h1 className="text-3xl font-bold">Войти в аккаунт</h1>

        <form onSubmit={handleSubmit} className="mt-6 space-y-2 w-full">
          <input
            type="text"
            id="name"
            name="name"
            placeholder="Ник"
            value={formData.name}
            onChange={handleChange}
            className="block mx-auto border rounded px-1 py-0.5"
          />

          <span className="w-full relative">
            <input
              type={showPassword ? "text" : "password"}
              id="password"
              name="password"
              placeholder="Пароль"
              autoComplete="off"
              value={formData.pword}
              minLength="8"
              maxLength="20"
              onChange={handleChange}
              className="border rounded px-1 py-0.5"
            />
            <button
              type="button"
              onClick={handleShowPassword}
              className="absolute right-2 translate-y-1 h-full text-gray-600 pointer cursor-pointer font-bold text-2xl rounded-full"
            >*
            </button>
          </span>

          {messageError}

          <Button type="submit" isDone={true}>Вход</Button>
        </form>
      </div>
    </Container>
  );
}
