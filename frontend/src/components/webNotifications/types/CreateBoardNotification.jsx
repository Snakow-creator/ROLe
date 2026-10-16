import { Notification } from "../notifications";

export class CreateBoardNotification extends Notification {
  constructor(duration) {
    super("Доска создана!", duration, "create_board");
  }

  renderBody() {
    return null;
  }
}
