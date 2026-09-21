import { useNotify } from "../../context/NotificationContext";

import { CreateItemNotification } from "../../components/webNotifications/types/CreateItemNotification";
import { BuyItemNotification } from "../../components/webNotifications/types/BuyitemNotification";
import { DeleteTaskNotification } from "../../components/webNotifications/types/DeleteTaskNotification";
import { addItem } from "../../services/apiService/items";



export function useItemsNotification () {
  const { push } = useNotify();

  const handleBuyItem = async (notice) => {
    push(new BuyItemNotification(notice));
  }

  const handleDeleteItem = async (notice) => {
    push(new DeleteTaskNotification(notice));
  }

  const createItem = async (formData) => {
    const res = await addItem(formData);
    push(new CreateItemNotification(res.data.notice));
  }

  return { handleBuyItem, handleDeleteItem, createItem }

}
