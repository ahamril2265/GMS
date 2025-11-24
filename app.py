from flask import Flask
from config import Config
from routes import main_bp
from admin.routes import admin_bp
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Create necessary directories
    os.makedirs('static/qr_codes', exist_ok=True)
    os.makedirs('static/uploads', exist_ok=True)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)



