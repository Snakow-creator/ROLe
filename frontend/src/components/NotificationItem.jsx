export function NotificationItem ({ notification, onRemove }) {
  return (
    <div
      onClick={() => onRemove(notification.id)}
      className="relative w-full flex-col items-start rounded-xl bg-white border border-[#E5E5E5] shadow p-4 pb-6 overflow-hidden cursor-pointer"
    >
      <span className="text-[#172033] font-bold text-lg">{notification.title}</span>
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
