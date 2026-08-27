import { getMessageTask } from "../hooks/messages"
import { useState } from "react"

export function NoticeContainer({ title }) {
  const [task] = useState(getMessageTask)

  return (
    (title && (
      <div className='absolute flex flex-col items-start space-y-2 rounded-xl w-[400px] right-[30px] bottom-[25px] bg-[#ffffff] border-[#E5E5E5] shadow p-4 pb-6'>
        <span className="text-[#172033] font-bold text-lg">{title}</span>
        <p className="block font-medium">{task}</p>
      </div>
    ))
  )
}


