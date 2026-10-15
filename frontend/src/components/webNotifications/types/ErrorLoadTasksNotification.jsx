import { ErrorNotification } from './ErrorNotification';
import { getRequestErrorMessage } from '../../../services/apiService/requestErrors';

export class ErrorLoadTasksNotification extends ErrorNotification {
  constructor(error, onRetry) {
    super('Не удалось загрузить доски', getRequestErrorMessage(error, 'Повторите загрузку досок и квестов.'), {
      type: 'error_load_tasks', dedupeKey: 'error_load_tasks', onRetry,
    });
  }
}
