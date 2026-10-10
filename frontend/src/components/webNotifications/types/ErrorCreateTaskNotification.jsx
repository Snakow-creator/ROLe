import { Notification } from "../notifications";

// требует только название задачи и длительность
export class ErrorCreateTaskNotification extends Notification {

  constructor(task, duration) {
    super("Ошибка при создании задачи", duration, "error_create_task")
  }

  renderBody() {
    return null
  }
}
