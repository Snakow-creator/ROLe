import { Notification } from '../notifications';

export class DeleteBoardNotification extends Notification {
  constructor(title) {
    super(`Доска «${title}» удалена`, undefined, 'delete_board');
  }

  renderBody() {
    return null;
  }
}
