import Button from "../Button";

import { useState } from "react"

import { fetchBuyItem } from "../../services/apiService/items";
import { deleteItem } from "../../services/apiService/items";

import { cn } from "../../hooks/utils";

export default function Item(creds) {
  const [showSubmit, setShowSubmit] = useState(false);

  const [trashSrc, setTrashSrc] = useState("/task/trash.png");

  const visibleSubmit = () => {
    setShowSubmit(true);
  }

  const hideSubmit = () => {
    setShowSubmit(false);
  }

  const buyItem = async () => {
    const res = await fetchBuyItem(creds.id);

    creds.onHandleBuyItemNotice(res.data.notice)
    creds.onUpdate();
  }

  const delItem = async (e) => {
    setTrashSrc("/task/trash_hover.png");

    e.preventDefault();
    const res = await deleteItem(creds.id);

    creds.onHandleDeleteItemNotice(res.data.notice)
    creds.onUpdate();
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
        "absolute right-14 font-bold transition-opacity duration-500",
        showSubmit ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
        onClick={buyItem}>
        приобрести
      </Button>
      {/* trash button */}
      <button
        className={cn("absolute right-6 z-[10000] transition-opacity duration-300 cursor-pointer h-[25px] w-[25px]",
          showSubmit ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
        onMouseEnter={() => { setTrashSrc("/task/trash_hover.png") }}
        onMouseLeave={() => { setTrashSrc("/task/trash.png") }}
        onMouseDown={() => { setTrashSrc("/task/trash_active.png") }}
        onClick={delItem}>

        <img src={trashSrc} />
      </button>
    </div>
  )
}
