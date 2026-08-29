let idCounter = 0

export class Notification {
  constructor(title, duration = 10000) {
    this.id = ++idCounter
    this.title = title
    this.duration = duration
    this.createdAt = Date.now()
  }

  renderBody() {
    throw new Error(`renderBody() не реализован в классе ${this.constructor.name}`)
  }
}
