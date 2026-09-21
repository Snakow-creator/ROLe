import Item from "../item/Item"

export default function ItemsList({ items, handleUpdate, onBuy, onDelete }) {
  return (
    <>
      {items.map((item, index) => (
        <Item
          key={item._id}
          id={item._id}
          index={index + 1}
          title={item.title}
          description={item.description}
          onUpdate={handleUpdate}
          price={item.price}
          type={item.type}
          onHandleBuyItemNotice={onBuy}
          onHandleDeleteItemNotice={onDelete}
        />
      ))}
    </>
  )
}
