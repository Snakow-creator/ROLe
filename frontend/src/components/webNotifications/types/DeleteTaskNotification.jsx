import { Notification } from "../notifications";

// требует только название задачи и длительность
export class DeleteTaskNotification extends Notification {

  constructor(task, duration) {
    super(task.title, duration, task.type)
  }

  renderBody() {
    return null
  }
}
