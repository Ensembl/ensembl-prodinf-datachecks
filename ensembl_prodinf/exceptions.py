class APIException(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload
        Exception.__init__(self, self.message, self.status_code)

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


class BadRequestError(APIException):
    pass
