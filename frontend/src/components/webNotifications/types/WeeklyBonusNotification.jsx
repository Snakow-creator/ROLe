import { Notification } from "../notifications";

// статический объект
export class WeeklyBonusNotification extends Notification {

  constructor(data, duration) {
    super(data.title, duration, data.type)
    this.data = data
    this.infoMessage = data.message
  }

  renderBody() {
    return (
      <div className="font-medium">
        <p>{this.infoMessage}</p>
      </div>
    )
  }
}
