import { Notification } from "../notifications";

export class CreatewItemMessage extends Notification {
  constructor(data, duration) {
    super(data.title, duration)
    this.data = data
  }

  renderBody() {
    return null
  }
}
