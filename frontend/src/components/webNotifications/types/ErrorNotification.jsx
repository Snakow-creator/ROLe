import { Notification } from '../notifications';

export class ErrorNotification extends Notification {
  constructor(title, message, { type = 'error_request', duration = 10000, onRetry, dedupeKey } = {}) {
    super(title, duration, type);
    this.message = message;
    this.onRetry = onRetry;
    this.dedupeKey = dedupeKey;
  }

  renderBody() {
    return (
      <div className="mt-2 text-sm font-normal">
        {this.message && <p>{this.message}</p>}
        {this.onRetry && (
          <button type="button" onClick={() => this.onRetry()} className="mt-3 cursor-pointer rounded-md border border-[#E5E9F0] px-3 py-1.5 font-semibold hover:bg-[#EEF2F7] focus-visible:outline-2 focus-visible:outline-blue-500">
            Повторить
          </button>
        )}
      </div>
    );
  }
}
