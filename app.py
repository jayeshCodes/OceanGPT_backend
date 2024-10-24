from flask import Flask

app = Flask(__name__)


@app.route('/')
def setup_check():  # put application's code here
    return 'Sever up and running'

@app.route('/chat')
def chat():
    """run chat functionalities here"""

@app.route('/upload')
def upload():
    """upload and save files here"""

@app.route('/download')
def download():
    """download and save files here"""

if __name__ == '__main__':
    app.run()
