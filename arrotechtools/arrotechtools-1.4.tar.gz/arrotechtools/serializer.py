from flask import make_response, jsonify


class Serializer:
    """Serialize data output.
    """

    def __init__(self):
        """Class constructor.
        """

    def serialize(self, response: list, message: str, status_code: int):
        """_summary_

        Args:
            response (list): _description_
            message (str): _description_
            status_code (int): _description_

        Returns:
            _type_: _description_
        """
        if status_code in (400, 401, 403, 404, 405, 500):
            return make_response(jsonify({
                "status": status_code,
                "message": message,
                "error": response
            }), status_code)
        return make_response(jsonify({
            "status": status_code,
            "message": message,
            "data": response
        }), status_code)

    def on_success(self, message: str, status_code: int):
        """_summary_

        Args:
            message (str): _description_
            status_code (int): _description_

        Returns:
            _type_: _description_
        """
        return make_response(jsonify({
            "status": status_code,
            "message": message,
        }), status_code)


class ErrorHandler:
    """Class error handler.
    """

    def __init__(self):
        """Class constructor.
        """

    def raise_error(self, message: str, status_code: int):
        """_summary_

        Args:
            message (str): _description_
            status_code (int): _description_

        Returns:
            _type_: _description_
        """
        return make_response(jsonify({
            "status": status_code,
            "message": message,
        }), status_code)

    def bad_request(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return make_response(jsonify({
            "status": "400",
            "message": "bad request"
        }), 400)

    def page_not_found(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return make_response(jsonify({
            "status": "404",
            "message": "resource not found"
        }), 404)

    def method_not_allowed(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return make_response(jsonify({
            "status": "405",
            "message": "method not allowed"
        }), 405)

    def internal_server_error(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        return make_response(jsonify({
            "status": "500",
            "message": "internal server error"
        }), 500)
