import { Link } from "react-router"
import { cn } from "../hooks/utils"

export default function LinkHeader (creds) {
  return (
    <Link to={creds.to}
      className={cn(
        "font-bold text-lg px-2 rounded-lg hover:bg-[#E9EDF3] active:bg-[#E5E9F0]",
        creds.className
      )}>
      {creds.children}
    </Link>
  )
}
