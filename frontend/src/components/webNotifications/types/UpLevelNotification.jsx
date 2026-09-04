import { Notification } from "../notifications"
import { getMessageLevel } from "../../../hooks/messages"

// требует только название задачи и длительность
export class UpLevelNotification extends Notification {
  constructor(task, duration) {
    super(task.title, duration)
    this.task = task
    this.infoMessage = task.message
    this.message = getMessageLevel() // random message level
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
