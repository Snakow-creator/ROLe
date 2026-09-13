import { Notification } from "../notifications";

// статический объект
export class CreateTaskNotification extends Notification {

  constructor(duration) {
    super("Квест создан!", duration)
  }

  renderBody() {
    return null
  }
}
