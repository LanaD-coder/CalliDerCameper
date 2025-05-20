from flask import Flask, render_template, request
from flask_babel import Babel, gettext as _

app = Flask(__name__)
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'locales'

babel = Babel(app)

@babel.localeselector
def get_locale():
    return request.args.get('lang') or 'en'

@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
