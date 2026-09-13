import { Notification } from "../notifications";


export class BuyItemNotification extends Notification {
  constructor(data, duration) {
    super(data.title, duration)
    this.data = data
    this.message = data.message
  }

  renderBody() {
    return (
      <div className="font-medium">
        <p>{this.message}</p>
      </div>
    )
  }
}
