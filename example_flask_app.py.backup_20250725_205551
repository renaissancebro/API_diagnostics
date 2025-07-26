from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World!'

@app.route('/users/<int:user_id>')
def get_user(user_id):
    return f'User {user_id}'

if __name__ == '__main__':
    app.run(debug=True)
