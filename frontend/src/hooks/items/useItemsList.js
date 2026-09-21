import { useState, useEffect, useCallback } from "react";
import { fetchItems } from "../../services/apiService/items";

export function useItemsList() {
  const [allItems, setAllItems] = useState([]);
  const [items, setItems] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const updateItems = useCallback(async () => {
    await fetchItems({
      setCurrentItems: data => {
        setItems(data);
        setAllItems(data);
        setIsLoading(false);
      }
    });
  }, []);

  useEffect(() => {
    updateItems();
  }, [updateItems])

  return { allItems, items, setItems, isLoading, updateItems}
}
