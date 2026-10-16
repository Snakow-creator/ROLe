import { useState, useCallback } from "react"

export function useNotifications() {
  const [notifications, setNotifications] = useState([])

  const remove = useCallback((id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))

  }, [])

  const push = useCallback((notificationInstance) => {
    setNotifications((prev) => {
      if (notificationInstance.dedupeKey && prev.some(n => n.dedupeKey === notificationInstance.dedupeKey)) return prev;
      return [...prev, notificationInstance];
    })
  }, [])

  const removeByKey = useCallback((dedupeKey) => {
    setNotifications(prev => prev.filter(n => n.dedupeKey !== dedupeKey));
  }, []);

  return { notifications, push, remove, removeByKey }
}
