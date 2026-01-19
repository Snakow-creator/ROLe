import Textarea from "../Textarea"
import Select from "../Select"
import Button from "../Button"

import { addItem } from "../../services/apiService/items"

import { useState } from "react"


export default function FormCreateItem(creds) {
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    min_level: 0,
    price: 0,
    type: "type",
    creator: creds.name,
  })

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev, [name]: value
    }))
  }

  const onSubmit = async (e) => {
    e.preventDefault();
    await addItem(formData);
    creds.onUpdate();
  }


  return (
    <form onSubmit={onSubmit}>
      <h1 className="text-xl font-bold text-left ml-2">Создать услугу</h1>

      <div className="flex justify-between mt-4">
        <Textarea
          className="bg-white appearance-none resize-none border border-[#F1F1F1] shadow sm:w-[404px] min-h-8 hover:outline-2 hover:outline-blue-400 rounded-md text-left p-1 px-2"
          placeholder="Введите название"
          max_length="100"
          name="title"
          focus={true}
          value={formData.title}
          onChange={handleChange}/>

        <Select
          name="type"
          value={formData.type}
          onChange={handleChange}
          className="sm:h-8">
            <option value="type" disabled>
              Тип задачи
            </option>
            <option value="rest">
              Отдых
            </option>
            <option value="money">
              Деньги
            </option>
            <option value="food">
              Еда
            </option>
        </Select>
      </div>

      <div className="flex justify-between mt-4">
        <Textarea
          className="bg-white appearance-none resize-none border border-[#F1F1F1] shadow sm:w-[404px] min-h-20 hover:outline-2 hover:outline-blue-400 rounded-md text-left p-1 px-2"
          placeholder="Введите описание"
          max_length="255"
          name="description"
          value={formData.description}
          onChange={handleChange}/>

        <div className="flex flex-col justify-between">
          <input type="text"
            className="bg-white rounded-md border border-[#F1F1F1] px-1 py-1 shadow text-sm w-[192px]"
            placeholder="Цена"
            name="price"
            onChange={handleChange} />

          <input type="text"
            className="bg-white rounded-md border border-[#F1F1F1] px-1 py-1 shadow text-sm w-[192px]"
            placeholder="Требуемый уровень"
            name="min_level"
            onChange={handleChange} />
        </div>
      </div>

      <Button type="submit"
        className="mt-4">
        Создать
      </Button>
    </form>
  )
}
