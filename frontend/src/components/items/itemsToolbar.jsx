// items toolbar filter items 
export default function ItemsToolbar ({ onChangeFilter, onChangeSort}) {
  return (
    <div className="flex items-center space-x-4 mt-2">
      {/* filter by type task */}
      <div className="relative inline-block">
        <select className="bg-white appearance-none px-2 pl-3 w-24 rounded-md border border-[#E8E8E8] hover:bg-[#F1F1F1] active:bg-[#E8E8E8] shadow"
                onChange={ onChangeFilter }>
          <option value="all">Все</option>
          <option value="rest">Отдых</option>
          <option value="money">Деньги</option>
          <option value="food">Еда</option>
        </select>
        <div className="pointer-events-none text-sm absolute right-2 inset-y-0 text-gray-600 flex items-center">
          ▼
        </div>
      </div>

      {/* sort by price */}
      <div className="relative inline-block">
        <select className="bg-white appearance-none px-2 pl-3 w-[192px] 2xl:w-[208px] rounded-md border border-[#E8E8E8] hover:bg-[#F1F1F1] active:bg-[#E8E8E8] shadow text-normal"
                onChange={ onChangeSort }>
          <option value="popular">Популярные</option>
          <option value="asc">По возрастанию</option>
          <option value="desc">По убыванию</option>
        </select>
        <div className="pointer-events-none text-sm absolute right-2 inset-y-0 text-gray-600 flex items-center">▼</div>
      </div>
    </div>
  )
}
