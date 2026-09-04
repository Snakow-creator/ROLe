let idCounter = 0

// object of notification
export class Notification {
  constructor(title, duration = 7000) {
    this.id = ++idCounter
    this.title = title
    this.duration = duration
    this.createdAt = Date.now()
  }

  renderBody() {
    throw new Error(`renderBody() не реализован в классе ${this.constructor.name}`)
  }
}
