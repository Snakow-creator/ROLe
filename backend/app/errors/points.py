class NotEnoughSpointsError(Exception):
    def __init__(self):
        message = "Не хватает Spoints"
        super().__init__(str(message))
