import { ErrorNotification } from './ErrorNotification';

// сообщение об ошибке и длительность
export class ErrorCreateTaskNotification extends ErrorNotification {

  constructor(message, duration) {
    super('Ошибка при создании задачи', message, { duration, type: 'error_create_task' });
  }
}
