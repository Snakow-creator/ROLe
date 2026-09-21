import { Notification } from "../notifications";

// требует только название задачи и длительность
export class TaskUnSubmitNotification extends Notification {
  constructor(task, duration) {
    super(task.title, duration)
    this.task = task
    this.infoMessage = task.message
  }

  renderBody() {
    return (
      <div className="font-medium">
        <p>{this.infoMessage}</p>
      </div>
    )
  }
}
