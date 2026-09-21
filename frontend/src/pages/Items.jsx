import Container from "../components/Container";
import Spinner from "../components/Spinner";

import { useState, useRef } from "react";

import { useItemsList } from "../hooks/items/useItemsList";
import { useItemsFilterSort } from "../hooks/items/useFilterSort";
import { useItemsNotification } from "../hooks/items/useItemsNotifications";
import { useOutsideClick } from "../hooks/items/useOutsideClick";

import ItemsToolbar from "../components/items/itemsToolbar";
import  ItemsList  from "../components/items/itemsList";
import ItemsCreateSelection from "../components/items/ItemsCreateSelection";


export default function Items() {
  const { allItems, items, setItems, isLoading, updateItems} = useItemsList();
  const { handleBuyItem, handleDeleteItem, createItem } = useItemsNotification();
  const { onChangeFilter, onChangeSort } = useItemsFilterSort(allItems, setItems);

  const [isFormCreateItem, setIsFromCreateItem] = useState(false);
  const formCreateItemRef = useRef(null);
  useOutsideClick(formCreateItemRef, isFormCreateItem, () => setIsFromCreateItem(false));

  if (isLoading) return <Spinner />;

  return (
    <Container>
      <div className="container bg-[#F9FAFE] mt-16 mx-auto w-[800px] 2xl:w-[1000px] 2xl:text-lg rounded-2xl py-8 px-8 shadow border border-[#E5E9F0]">
        <h1 className="text-2xl 2xl:text-3xl font-bold">
          Магазин услуг
        </h1>

        <ItemsToolbar onChangeFilter={onChangeFilter} onChangeSort={onChangeSort} />
        <hr lassName="mt-4 shadow-xs"/>

        <div className="space-y-4 mt-4">
          {/* create item form */}
          <ItemsCreateSelection
            isFormOpen={isFormCreateItem}
            setIsFormOpen={setIsFromCreateItem}
            formRef={formCreateItemRef}
            onSubmit={createItem}
            onUpdate={updateItems}
          />
          {/* get formated items list */}
          <ItemsList
            items={items}
            handleUpdate={updateItems}
            onBuy={handleBuyItem}
            onDelete={handleDeleteItem}
          />
        </div>
      </div>
    </Container>
  );
}
