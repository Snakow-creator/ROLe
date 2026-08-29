import { useState, useCallback, useRef } from "react"

let idCounter = 0

export function useNotifications() {
  const [notifications, setNotifications] = useState([])
  const timers = useRef({})

  const remove = useCallback((id) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id))
    clearTimeout(timers.current[id])
    delete timers.current[id]

  }, [])

  const push = useCallback((notificationInstance) => {
    setNotifications((prev) => [...prev, notificationInstance])
    timers.current[notificationInstance.id] = setTimeout(
      () => remove(notificationInstance.id),
      notificationInstance.duration
    )
  }, [remove])

  return { notifications, push, remove }
}
