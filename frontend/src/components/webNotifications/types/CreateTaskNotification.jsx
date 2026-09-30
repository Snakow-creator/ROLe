import { Notification } from "../notifications";

// статический объект
export class CreateTaskNotification extends Notification {

  constructor(duration) {
    super("Квест создан!", duration, "create_task")
  }

  renderBody() {
    return null
  }
}
