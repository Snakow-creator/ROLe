import Button from "../components/Button";
import Container from "../components/Container";

import { useRef } from "react";
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
  const [items, setItems] = useState([]);

  useEffect(() => {
    const setCurrentItems = (data) => {
      setItems(data);
    }

    fetchItems(setCurrentItems);
  }, []);

  return (
    <Container>
      <div className="container bg-[#F9FAFE] mt-16 mx-auto w-[800px] rounded-2xl py-8 px-8 shadow border border-[#E5E9F0]">
        <h1 className="text-2xl font-bold">
          Магазин услуг
        </h1>

      <div className="space-y-4 mt-8">
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
