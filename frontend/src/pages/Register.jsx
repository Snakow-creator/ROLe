import { useState } from "react";
import { register } from "../services/apiService/auth";

import { MessageError } from "../components/Message";
import Button from "../components/Button";
import Container from "../components/Container";
import { cn } from "../hooks/utils";


function InputPassword({ name, placeholder, value, onChange, className }) {
  const [showPassword, setShowPassword] = useState(false);

  const handleShowPassword = () => {
    setShowPassword(!showPassword)
  }

  return (
    <div>
      <span className="relative">
        <input
          type={showPassword ? "text" : "password"}
          name={name}
          placeholder={placeholder}
          value={value}
          minLength="8"
          maxLength="20"
          onChange={onChange}
          className={cn(
            "border rounded px-1 py-0.5 w-[226px] 2xl:w-[244px]",
            className)} />
        <button
          type="button"
          onClick={handleShowPassword}
          className="absolute right-2 translate-y-1 h-full text-gray-600 pointer font-bold text-2xl rounded-full"
        >*
        </button>
      </span>
    </div>
  )
}

export default function Register() {
  const [formData, setFormData] = useState({
    name: "",
    password1: "",
    password2: ""
  })
  const [message, setMessage] = useState('');
  const [messageNameError, setMessageNameError] = useState(<></>);
  const [messagePasswordError, setMessagePasswordError] = useState(<></>);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev, [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const changeMessageNameError = () => {
      setMessageNameError(
        <MessageError>
          Пользователь с таким ником уже существует
        </MessageError>
      )
    }
    const changeMessagePasswordError = () => {
      setMessagePasswordError(
        <MessageError>
          Пароли не совпадают
        </MessageError>
      )
    }

    const successSubmit = () => {
      // clear error messages
      setMessageNameError(<></>);
      setMessagePasswordError(<></>);

      setMessage(
        <p className="text-green-600 text-center">
          Вы успешно зарегистрировались
        </p>
      );
    }

    await register({
      formData: formData,
      changeMessageNameError: changeMessageNameError,
      changeMessagePasswordError: changeMessagePasswordError,
      successSubmit: successSubmit,
    });

  }


  return (
    <Container>
      <div className="container sm:w-[50%] sm:min-w-[324px] sm:max-w-[400px] 2xl:max-w-[500px] 2xl:text-lg mx-auto rounded-2xl lg:mt-16 mt-4 pt-4 pb-6 2xl:pt-6 2xl:pb-8 bg-white shadow-sm">
        <h1 className="text-3xl 2xl:text-4xl font-extrabold">Регистрация</h1>

        <form onSubmit={handleSubmit} className="mt-4 space-y-2">
          <input
            type="text"
            placeholder="Ник"
            className="block mx-auto border rounded px-1 py-0.5 w-[226px] 2xl:w-[244px]"
            name="name"
            value={formData.name}
            onChange={handleChange}
          />

          {messageNameError}

          <InputPassword
            name="password1"
            placeholder="Пароль"
            value={formData.password1}
            onChange={handleChange} />

          <InputPassword
            name="password2"
            placeholder="Подтвердите пароль"
            value={formData.password2}
            onChange={handleChange} />

          {messagePasswordError}

          <Button type="submit" isDone={true}>Зарегистрироваться</Button>
          {message && <p className="text-green-600 text-bold">{message}</p>}
        </form>
      </div>
    </Container>
  );
}
