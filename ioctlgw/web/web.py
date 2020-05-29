from flask import Flask, render_template, request, flash, Markup
from flask_bootstrap import Bootstrap

app = Flask(__name__)
app.secret_key = 'dev'

# set default button sytle and size, will be overwritten by macro parameters
app.config['BOOTSTRAP_BTN_STYLE'] = 'primary'
app.config['BOOTSTRAP_BTN_SIZE'] = 'sm'

bootstrap = Bootstrap(app)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/nav', methods=['GET', 'POST'])
def test_nav():
    return render_template('nav.html')

if __name__ == '__main__':
    app.run(debug=True)