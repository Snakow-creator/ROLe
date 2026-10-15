import { Link } from 'react-router-dom';
import { ErrorNotification } from './ErrorNotification';

export class SessionExpiredNotification extends ErrorNotification {
  constructor() {
    super('Сессия завершена', 'Войдите снова, чтобы продолжить работу.', {
      type: 'error_session_expired', duration: 15000, dedupeKey: 'error_session_expired',
    });
  }

  renderBody() {
    return (
      <div className="mt-2 text-sm font-normal">
        <p>{this.message}</p>
        <Link to="/login" className="mt-3 inline-block font-semibold text-blue-600 underline underline-offset-2">Войти в аккаунт</Link>
      </div>
    );
  }
}
