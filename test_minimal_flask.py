from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    print("HOME ROUTE CALLED!")
    return "Hello from Flask!"

if __name__ == '__main__':
    print("Starting minimal Flask...")
    app.run(host='127.0.0.1', port=5001, debug=True)
