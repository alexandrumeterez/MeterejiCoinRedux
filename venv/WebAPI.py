import Blockchain
from flask import Flask, jsonify, request
from uuid import uuid4

# Instantiate node
app = Flask(__name__)

# Generate unique address for node
node_identifier = str(uuid4()).replace('-', '')

blockchain = Blockchain.Blockchain()


@app.route('/')
def welcome():
    return "Welcome to Meterejicoin!"


@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block

    # We must receive a reward for finding the proof.
    # The sender is "0" to signify that this node has mined a new coin.
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Forge the new Block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(previous_hash)
    nonce = blockchain.proof_of_work(block)
    block['nonce'] = nonce
    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'nonce': block['nonce'],
        'previous_hash': block['previous_hash'],
        'hash': blockchain.hash(block)
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    required = ['sender', 'recipient', 'amount']
    if values is None:
        return "Bad request", 400
    if not all(k in values for k in required):
        return "Missing values", 400

    # Create new transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to block {index}'}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200


@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    if values is None:
        return "Bad request", 400
    nodes = values.get('nodes')
    if nodes is None:
        return "Invalid nodes list", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': 'New node has been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 200


@app.route('/nodes/resolve', methods=['GET'])
def resolve_chain():
    replaced = blockchain.resolve_conflict()

    if replaced:
        response = {
            'message': 'We have a new chain',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is good',
            'chain': blockchain.chain
        }
    return jsonify(response), 200


@app.route('/nodes', methods=['GET'])
def get_nodes():
    response = {
        'message': "Current nodes:",
        'nodes': list(blockchain.nodes)
    }
    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port)