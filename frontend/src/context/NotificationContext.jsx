import { useContext, createContext } from "react";
import { useNotifications } from "../hooks/useNotifications";
import { NotificationItem } from "../components/NotificationItem";

const NotificationContext = createContext(null);

export function NotificationProvider({ children }) {
  const { notifications, push, remove } = useNotifications();

  return (
    <NotificationContext.Provider value={{push, remove}}>
      {children}
      <div className="fixed flex flex-col-reverse items-start space-y-2 space-y-reverse right-[30px] bottom-[25px] w-[400px] z-50">
        {notifications.map((n) => (
          <NotificationItem key={n.id} notification={n} onRemove={remove} />
        ))}
      </div>
    </NotificationContext.Provider>
  )
}

export function useNotify() {
  return useContext(NotificationContext)
}
