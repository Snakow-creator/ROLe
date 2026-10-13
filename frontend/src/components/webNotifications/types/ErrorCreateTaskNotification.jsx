import { Notification } from "../notifications";

// сообщение об ошибке и длительность
export class ErrorCreateTaskNotification extends Notification {

  constructor(message, duration) {
    super("Ошибка при создании задачи", duration, "error_create_task")
    this.message = message;
  }

  renderBody() {
    return this.message ? <p className="mt-2 text-sm font-normal">{this.message}</p> : null
  }
}
