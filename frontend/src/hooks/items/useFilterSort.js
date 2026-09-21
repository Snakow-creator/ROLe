// Filter and sort
export function useItemsFilterSort(allItems, setItems) {
  // change filter
  const onChangeFilter = (e) => {
    setItems(
      e.target.value == "all"
      ? allItems
      : allItems.filter(item => item.type === e.target.value)
    );
  };

  // sort items
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
  };

  return { onChangeFilter, onChangeSort };
}
