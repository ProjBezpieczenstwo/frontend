from flask import Flask, render_template
from blueprints.auth import auth_bp
from blueprints.lessons import lessons_bp
from blueprints.reviews import reviews_bp
from blueprints.admin import admin_bp

app = Flask(__name__)
app.config.from_object('config.Config')

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(lessons_bp, url_prefix='/lessons')
app.register_blueprint(reviews_bp, url_prefix='/reviews')
app.register_blueprint(admin_bp, url_prefix='/admin')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
