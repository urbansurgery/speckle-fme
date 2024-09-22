class TestLogger:
  def __init__(self):
    self.messages = []

  def logMessageString(self, message):
    self.messages.append(message)

  def get_messages(self):
    return self.messages
