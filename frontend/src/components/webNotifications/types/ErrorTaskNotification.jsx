import { ErrorNotification } from './ErrorNotification';
import { getRequestErrorMessage } from '../../../services/apiService/requestErrors';

const titles = {
  create: 'Не удалось создать квест',
  complete: 'Не удалось завершить квест',
  uncomplete: 'Не удалось отменить выполнение квеста',
  delete: 'Не удалось удалить квест',
};

export class ErrorTaskNotification extends ErrorNotification {
  constructor(action, error) {
    super(titles[action], getRequestErrorMessage(error, 'Попробуйте ещё раз.'), {
      type: `error_task_${action}`,
    });
  }
}
