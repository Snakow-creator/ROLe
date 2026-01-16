import Button from "../components/Button";
import Container from "../components/Container";

import { useState, useEffect } from "react";

import { fetchBuyItem, fetchItems } from "../services/apiService/items";
import { cn } from "../hooks/utils";


function Item(creds) {
  const [showSubmit, setShowSubmit] = useState(false);

  const visibleSubmit = () => {
    setShowSubmit(true);
  }

  const hideSubmit = () => {
    setShowSubmit(false);
  }

  const buyItem = async () => {
    const res = await fetchBuyItem(creds.id);

    console.log(res);
  }



  return (
    <div
      className="relative flex items-center space-x-1 bg-[#ffffff] text-lg rounded-xl px-6 py-3 w-full border border-[#F1F1F1] hover:outline-2 hover:outline-blue-400 box-border shadow transition-transform"
      onMouseEnter={() => { visibleSubmit() }}
      onMouseLeave={() => { hideSubmit() }}>

      <span className="font-bold">
        {creds.index}.
      </span>

      <span>
        {creds.title}
      </span>

      <span className={cn(
        "absolute right-6 font-bold transition-opacity",
        showSubmit ? "opacity-0 pointer-events-none" : "opacity-100"
        )}>
        {creds.price.toFixed(1)}
      </span>

      <Button className={cn(
        "absolute right-6 font-bold transition-opacity duration-500",
        showSubmit ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
        onClick={buyItem}>
        приобрести
      </Button>
    </div>
  )
}

export default function Items() {
  const [allItems, setAllItems] = useState([]);
  const [items, setItems] = useState([]);

  useEffect(() => {
    const setCurrentItems = (data) => {
      setItems(data);
      setAllItems(data);
    }

    fetchItems(setCurrentItems);
  }, []);

  const onChangeFilter = (e) => {
    setItems(
      e.target.value == "all"
      ? allItems
      : allItems.filter(item => item.type === e.target.value)
    );
  };

  const onChangeSort = (e) => {
    if (e.target.value == "popular") {
      setItems(allItems);
      return;
    }
    setItems(
      e.target.value == "asc"
      ? [...allItems].sort((a, b) => a.price - b.price)
      : [...allItems].sort((a, b) => b.price - a.price)
    )
  }

  return (
    <Container>
      <div className="container bg-[#F9FAFE] mt-16 mx-auto w-[800px] rounded-2xl py-8 px-8 shadow border border-[#E5E9F0]">
        <h1 className="text-2xl font-bold">
          Магазин услуг
        </h1>

      <div className="flex items-center space-x-4 mt-2">
        {/* filter by type task */}
        <div className="relative inline-block">
          <select className="bg-white appearance-none px-2 pl-3 w-24 rounded-md border border-[#E8E8E8] hover:bg-[#F1F1F1] active:bg-[#E8E8E8] shadow"
                  onChange={ onChangeFilter }>
            <option value="all">
              Все
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
          </select>
          <div className="pointer-events-none text-sm absolute right-2 inset-y-0 text-gray-600 flex items-center">
            ▼
          </div>
        </div>

        {/* sort by price */}
        <div className="relative inline-block">
          <select className="bg-white appearance-none px-2 pl-3 w-48 rounded-md border border-[#E8E8E8] hover:bg-[#F1F1F1] active:bg-[#E8E8E8] shadow text-normal"
                  onChange={ onChangeSort }>
            <option value="popular">
              Популярные
            </option>
            <option value="asc">
              По возрастанию
            </option>
            <option value="desc">
              По убыванию
            </option>
          </select>
          <div className="pointer-events-none text-sm absolute right-2 inset-y-0 text-gray-600 flex items-center">
            ▼
          </div>
        </div>

      </div>

      <hr className="mt-4 shadow-xs" />

      <div className="space-y-4 mt-4">
        <button
          className="relative flex items-center space-x-1 bg-[#ffffff] text-[#67748A] cursor-pointer font-bold shadow text-lg rounded-xl px-6 py-3 w-full border border-[#F1F1F1] hover:bg-[#F7F7F7] active:bg-[#F1F1F1]"
          type="button"
          onClick={() => {}}>
            ＋ Добавить услугу
        </button>

        {items.map((item, index) => (
          <Item
            key={item._id}
            id={item._id}
            index={index + 1}
            title={item.title}
            description={item.description}
            price={item.price}
            type={item.type}
          />
        ))}
      </div>


      </div>
      {/* <h1 className="text-2xl font-extrabold">Магазин услуг</h1>
      <div className="space-y-4">
        {items.map((item, index) => (
          <Item
            key={item._id}
            id={item._id}
            index={index + 1}
            title={item.title}
            description={item.description}
            price={item.price}
            type={item.type}
          />
        ))}
      </div> */}
    </Container>
  );
}
