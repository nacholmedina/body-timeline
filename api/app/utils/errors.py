from flask import jsonify


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify(error="Bad Request", message=str(e.description)), 400

    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify(error="Unauthorized", message="Authentication required"), 401

    @app.errorhandler(403)
    def forbidden(e):
        return jsonify(error="Forbidden", message="Insufficient permissions"), 403

    @app.errorhandler(404)
    def not_found(e):
        return jsonify(error="Not Found", message="Resource not found"), 404

    @app.errorhandler(413)
    def too_large(e):
        return jsonify(error="Payload Too Large", message="File too large"), 413

    @app.errorhandler(422)
    def unprocessable(e):
        return jsonify(error="Unprocessable Entity", message=str(e.description)), 422

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify(error="Internal Server Error", message="An unexpected error occurred"), 500


def validation_error(message: str, field: str | None = None):
    body = {"error": "Validation Error", "message": message}
    if field:
        body["field"] = field
    return jsonify(body), 422


def api_error(message: str, status: int = 400):
    return jsonify(error="Error", message=message), status
