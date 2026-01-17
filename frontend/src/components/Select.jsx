import { cn } from "../hooks/utils";

export default function Select(creds) {
  return (
    <div className="flex justify-between relative">
      <select
        className={cn(
          "bg-white appearance-none px-2 pl-3 w-48 rounded-md border border-[#E8E8E8] hover:bg-[#F1F1F1] active:bg-[#E8E8E8] shadow text-normal",
          creds.className
        )}
        onChange={creds.onChange}
        name={creds.name}
        value={creds.value}>
        {creds.children}
      </select>
      <div className="absolute text-sm translate-y-1/2 right-2 text-gray-600">
        ▼
      </div>
    </div>
  )
}
