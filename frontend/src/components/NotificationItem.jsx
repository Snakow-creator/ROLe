import { useEffect, useState } from "react"

import { cn } from "../hooks/utils"

// notification container
export function NotificationItem ({ notification, onRemove, isError }) {
  const [isLeaving, setIsLeaving] = useState(false)
  const exitDuration = 300 // мс, должно совпадать с длительностью slideOutRight

  // exitDuration function
  useEffect(() => {
    const leaveTimer = setTimeout(() => {
      setIsLeaving(true)
    }, notification.duration - exitDuration)

    return () => clearTimeout(leaveTimer)
  }, [notification.duration])

  // delete notification, with animation
  const handleAnimationEnd = (event) => {
    if (
      event.target === event.currentTarget &&
      event.animationName === "notification-exit"
    ) {
      onRemove(notification.id)
    }
  }

  const handleClose = () => {
    setIsLeaving(true) // animation is working even you close notice yourself
  }

  return (
    <div
      role={isError ? 'alert' : 'status'}
      className="relative w-full flex-col items-start rounded-xl bg-white border border-[#E5E5E5] shadow p-4 pb-6 overflow-hidden"
      style={{ animation: isLeaving
        ? `notification-exit ${exitDuration}ms ease-in-out forwards`
        : "notification-enter 0.3s ease-in-out forwards"
      }}
      onAnimationEnd={handleAnimationEnd}
    >
      <button
        type="button"
        onClick={handleClose}
        disabled={isLeaving}
        className="absolute top-2 right-2 flex h-7 w-7 items-center justify-center rounded-full text-gray-400 cursor-pointer transition-colors hover:bg-gray-100 hover:text-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-400 disabled:pointer-events-none"
        aria-label="Закрыть уведомление"
      >
        <svg
          viewBox="0 0 24 24"
          className="h-4 w-4"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          aria-hidden="true"
        >
          <path d="M6 6l12 12M18 6L6 18" />
        </svg>
      </button>
      <span className="block pr-8 text-[#172033] font-bold text-lg">{notification.title}</span>
      {notification.renderBody()}

      <div className="absolute bottom-0 left-0 h-1 bg-[#E5E5E5] w-full">
        <div
          className={cn(
            "bg-green-500 h-full animate-shrink",
            isError && "bg-red-500"
          )}
          style={{ animationDuration: `${notification.duration}ms` }}
        />
      </div>
    </div>
  )
}
