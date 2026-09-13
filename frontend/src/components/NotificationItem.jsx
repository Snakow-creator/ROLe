import { useEffect, useState } from "react"

// notification container
export function NotificationItem ({ notification, onRemove }) {
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
  const handleAnimationEnd = () => {
    if (isLeaving) {
      onRemove(notification.id)
    }
  }

  const handleClose = () => {
    setIsLeaving(true) // animation is working even you close notice yourself
  }

  return (
    <div
      className="relative w-full flex-col items-start rounded-xl bg-white border border-[#E5E5E5] shadow p-4 pb-6 overflow-hidden"
      style={{ animation: isLeaving
        ? `notification-exit ${exitDuration}ms ease-in-out forwards`
        : "notification-enter 0.3s ease-in-out forwards"
      }}
      onAnimationEnd={handleAnimationEnd}
    >
      <button
        onClick={handleClose}
        className="absolute top-2 right-2 w-5 h-5 flex items-center justify-center text-gray-400 hover:text-gray-700 cursor-pointer text-lg"
        aria-label="Закрыть уведомление"
        >
        ✕
      </button>
      <span className="text-[#172033] font-bold text-lg pr-6">{notification.title}</span>
      {notification.renderBody()}

      <div className="absolute bottom-0 left-0 h-1 bg-[#E5E5E5] w-full">
        <div
          className="bg-green-500 h-full animate-shrink"
          style={{ animationDuration: `${notification.duration}ms` }}
        />
      </div>
    </div>
  )
}
