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
      <div className="container sm:w-[50%] sm:min-w-[324px] sm:max-w-[400px] 2xl:max-w-[500px] mx-auto 2xl:text-lg rounded-2xl md:mt-16 mt-4 pt-4 pb-6 2xl:pt-6 2xl:pb-8 bg-white shadow-sm">

        <h1 className="text-3xl font-bold">Войти в аккаунт</h1>

        <form onSubmit={handleSubmit} className="mt-6 space-y-2">
          <input
            type="text"
            id="name"
            name="name"
            placeholder="Ник"
            value={formData.name}
            onChange={handleChange}
            className="block mx-auto border rounded px-1 py-0.5 w-[226px] 2xl:w-[244px]"
          />

          <span className="relative">
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
              className="border rounded px-1 py-0.5 w-[226px] 2xl:w-[244px]"
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
