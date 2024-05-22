from app import app
from flask import jsonify, request
from app.utils import create_token

@app.route('/')
def index():
    return "Welcome to Solana Token Creation API"

@app.route('/create_token', methods=['POST'])
def create_token_route():
    data = request.get_json()
    token_name = data['token_name']
    token_symbol = data['token_symbol']
    token_decimals = data['token_decimals']
    token_supply = data['token_supply']

    result = create_token(token_name, token_symbol, token_decimals, token_supply)
    return jsonify(result)