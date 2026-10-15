import { useContext, createContext, useLayoutEffect } from "react";
import { useNotifications } from "../hooks/useNotifications";
import { NotificationItem } from "../components/NotificationItem";
import api from '../services/apiService/api';
import { isSessionExpiredError } from '../services/apiService/requestErrors';
import { SessionExpiredNotification } from '../components/webNotifications/types/SessionExpiredNotification';

const NotificationContext = createContext(null);

export function NotificationProvider({ children }) {
  const { notifications, push, remove, removeByKey } = useNotifications();

  // Subscribe before child effects start their initial API requests.
  useLayoutEffect(() => {
    const notifiedTokens = new Set();
    const interceptor = api.interceptors.response.use(response => response, error => {
      if (isSessionExpiredError(error)) {
        const headers = error.config.headers;
        const token = headers.Authorization || headers.authorization;
        if (!notifiedTokens.has(token)) {
          notifiedTokens.add(token);
          push(new SessionExpiredNotification());
        }
      }
      return Promise.reject(error);
    });
    return () => api.interceptors.response.eject(interceptor);
  }, [push]);

  return (
    <NotificationContext.Provider value={{push, remove, removeByKey}}>
      {children}
      <div className="fixed flex flex-col-reverse items-start space-y-2 space-y-reverse right-[30px] bottom-[25px] w-[400px] max-w-[calc(100vw-60px)] z-50">
        {notifications.map((n) => (
          <NotificationItem key={n.id} notification={n} onRemove={remove} isError={n.type.startsWith("error") ? true : false} />
        ))}
      </div>
    </NotificationContext.Provider>
  )
}

export function useNotify() {
  return useContext(NotificationContext)
}
