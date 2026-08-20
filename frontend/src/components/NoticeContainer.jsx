import { getMessageTask } from "../hooks/messages"

export function NoticeContainer(creds) {
  return (
    (creds.title && (
      <div className='absolute flex flex-col items-start space-y-2 rounded-xl w-[400px] right-[30px] bottom-[25px] bg-[#ffffff] border-[#E5E5E5] shadow p-4 pb-6'>
        <span className="text-[#172033] font-bold text-lg">{creds.title}</span>
        <p className="block font-medium">{getMessageTask()}</p>
      </div>
    ))
  )
}


