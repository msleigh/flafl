"""Exceptions"""


class InvalidUsage(Exception):
    """Badly-formed payload."""

    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        return_value = dict(self.payload or ())
        return_value["status code"] = self.status_code
        return_value["message"] = self.message
        return return_value
