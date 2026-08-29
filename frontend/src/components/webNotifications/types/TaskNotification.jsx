import { Notification } from "../notifications";
import { getMessageTask } from "../../../hooks/messages";

// требует только название задачи и длительность
export class TaskNotification extends Notification {
  constructor(task, duration) {
    super(task.title, duration)
    this.task = task
    this.infoMessage = task.message
    this.message = getMessageTask()
  }

  renderBody() {
    return (
      <div className="font-medium">
        <p>{this.message}</p>
        <p>{this.infoMessage}</p>
      </div>
    )
  }
}
