import Textarea from "./Textarea"
import Button from "./Button"

import { addTask } from "../services/apiService/tasks"

import { useState } from "react"
import { useLocation, useNavigate } from "react-router"

export default function FormCreateTask(creds) {
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    type: creds.type,
    date: new Date().toISOString().split('T')[0],
  })

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev, [name]: value
    }))
  }

  const onSubmit = async (e) => {
    e.preventDefault();
    const res = await addTask(formData);

    creds.onClickCancelButton();
    creds.onUpdate();
  }

  return (
    <form onSubmit={onSubmit}
      className="mt-2">

      <Textarea
        className="bg-white appearance-none resize-none border border-[#F1F1F1] shadow w-full min-h-16 hover:outline-2 hover:outline-blue-400 rounded-md text-left p-1 px-2"
        placeholder="Введите заголовок квеста"
        maxLength="100"
        name="title"
        id="title"
        focus={true}
        value={formData.title}
        onChange={handleChange} />

      <Textarea
        className="bg-white appearance-none resize-none border border-[#F1F1F1] shadow mt-1 w-full min-h-24 hover:outline-2 hover:outline-blue-400 rounded-md text-left p-1 px-2"
        placeholder="Введите описание квеста"
        maxLength="255"
        name="description"
        id="description"
        value={formData.description}
        onChange={handleChange} />

      <div className="flex items-center justify-between">
        {/* create task */}
        <Button
          type="submit"
          className="ml-2 mt-0 text-sm p-1 px-2">
          Добавить
        </Button>

        {/* cancel */}
        <button type="button"
          onClick={creds.onClickCancelButton}
          className="text-2xl text-[#7C8AA0] mr-1 w-6 h-8 cursor-pointer hover:bg-[#EEF2F7] active:bg-[#E5E9F0] hover:shadow active:shadow rounded-md">
          ╳
        </button>

      </div>

    </form>
  )
}
