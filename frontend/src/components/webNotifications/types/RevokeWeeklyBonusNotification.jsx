import { Notification } from "../notifications";

// статический объект
export class RevokeWeeklyBonusNotification extends Notification {

  constructor(data, duration) {
    super(data.title, duration)
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
