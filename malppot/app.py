from flask import Flask, jsonify, request

app = Flask(__name__)

# 기본 엔드포인트
@app.route('/')
def home():
    return jsonify({"message": "Welcome to Flask API Server!"})

# GET 요청 핸들링
@app.route('/api/data', methods=['GET'])
def get_data():
    sample_data = {
        "id": 1,
        "name": "Sample Item",
        "description": "This is a sample API response."
    }
    return jsonify(sample_data)

# POST 요청 핸들링
@app.route('/api/data', methods=['POST'])
def post_data():
    data = request.get_json()
    return jsonify({"received_data": data, "message": "Data received successfully!"})

# PUT 요청 핸들링
@app.route('/api/data/<int:item_id>', methods=['PUT'])
def update_data(item_id):
    data = request.get_json()
    return jsonify({"item_id": item_id, "updated_data": data})

# DELETE 요청 핸들링
@app.route('/api/data/<int:item_id>', methods=['DELETE'])
def delete_data(item_id):
    return jsonify({"message": f"Item {item_id} deleted successfully!"})

if __name__ == '__main__':
    app.run(debug=True)
