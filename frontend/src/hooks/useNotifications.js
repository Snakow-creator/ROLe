import { useState, useCallback } from "react"

export function useNotifications() {
  const [notifications, setNotifications] = useState([])

  const remove = useCallback((id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))

  }, [])

  const push = useCallback((notificationInstance) => {
    setNotifications((prev) => [...prev, notificationInstance])
  }, [])

  return { notifications, push, remove }
}
