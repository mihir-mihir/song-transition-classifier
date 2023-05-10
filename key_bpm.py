from flask import Flask, request, jsonify

from main import process1, process2


app = Flask(__name__)

@app.route('/')
def index():
    return jsonify({'message': 'Welcome'})


# data collection
@app.route('/matcher', methods=['POST'])
def data_collector():
    data = request.json
    labels
    return labels


if __name__ == '__main__':
    app.run(port=5000, debug=True)