from flask import Flask
from models.database import init_db


def create_app():
    app = Flask(__name__)
    app.secret_key = 'smart-campus-secret-key-2026'

    init_db()

    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.complaints import complaints_bp
    from routes.notices import notices_bp
    from routes.chatbot import chatbot_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(complaints_bp)
    app.register_blueprint(notices_bp)
    app.register_blueprint(chatbot_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
