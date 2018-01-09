import Blockchain
from flask import Flask, jsonify, request
from uuid import uuid4
import sqlite3
import hashlib

# Instantiate node
app = Flask(__name__)

# Generate unique address for node
# node_identifier = str(uuid4()).replace('-', '')

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

    # Add to database
    conn = sqlite3.connect("/home/alex/PycharmProjects/MeterejiCoin/Databases/Addresses")
    c = conn.cursor()
    c.execute("UPDATE tbl1 SET amount=amount+? WHERE private_key=?;", (1, node_identifier))
    conn.commit()
    conn.close()

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

    sender_hash = hashlib.sha256(values['sender'].encode('utf-8')).hexdigest()
    recipient_hash = hashlib.sha256(values['recipient'].encode('utf-8')).hexdigest()
    conn = sqlite3.connect("/home/alex/PycharmProjects/MeterejiCoin/Databases/Addresses")
    c = conn.cursor()
    print(sender_hash)
    found = c.execute("""SELECT EXISTS(SELECT 1 FROM tbl1 WHERE private_key=?);""", (sender_hash,)).fetchall()
    if found[0][0] is False:
        conn.commit()
        conn.close()
        return "Sender not found!", 400
    found = c.execute("""SELECT EXISTS(SELECT 1 FROM tbl1 WHERE private_key=?);""", (recipient_hash,)).fetchall()
    if found[0][0] is False:
        conn.commit()
        conn.close()
        return "Recipient not found!", 400

    # Get cash from sender's wallet
    print(sender_hash)
    sender_amount = c.execute("""SELECT amount FROM tbl1 WHERE private_key=?;""", (sender_hash,)).fetchone()[0]
    if sender_amount > int(values['amount']):
        c.execute("UPDATE tbl1 SET amount=amount+? WHERE private_key=?;", (int(values['amount']), recipient_hash))
        c.execute("UPDATE tbl1 SET amount=amount-? WHERE private_key=?;", (int(values['amount']), sender_hash))
        conn.commit()
        conn.close()
        # Create new transaction
        index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])

        response = {'message': f'Transaction will be added to block {index}'}
        return jsonify(response), 201
    response = {'message': 'Bad transaction'}
    return jsonify(response), 400


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
    #
    if values is None:
        return "Bad request", 400

    private_key = values.get('private_key')
    if private_key is None:
        return "Invalid private key", 400

    key = hashlib.sha256(str(private_key).encode('utf-8')).hexdigest()
    conn = sqlite3.connect("/home/alex/PycharmProjects/MeterejiCoin/Databases/Addresses")
    c = conn.cursor()
    found = c.execute("""SELECT EXISTS(SELECT 1 FROM tbl1 WHERE private_key=?);""", (key,)).fetchall()
    print(found)
    if found[0][0] == 1:
        conn.commit()
        conn.close()
        response = {
            'message': 'Node already exists!',
        }
        return jsonify(response), 400

    print(private_key)
    public_key = hashlib.sha256(str(private_key).encode('utf-8')).hexdigest()
    blockchain.register_node(public_key)

    # Add to database
    conn = sqlite3.connect("/home/alex/PycharmProjects/MeterejiCoin/Databases/Addresses")
    c = conn.cursor()
    c.execute("""INSERT INTO tbl1 VALUES (?,?);""", (public_key, 0))
    conn.commit()
    conn.close()

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


@app.route('/login', methods=['POST'])
def login_user():
    global node_identifier
    values = request.get_json()
    if values is None:
        return "Bad request", 400
    key = values['private_key']
    public_key = hashlib.sha256(str(key).encode('utf-8')).hexdigest()
    # Add to database
    conn = sqlite3.connect("/home/alex/PycharmProjects/MeterejiCoin/Databases/Addresses")
    c = conn.cursor()
    found = c.execute("""SELECT EXISTS(SELECT 1 FROM tbl1 WHERE private_key=?);""", (public_key,)).fetchall()
    if found[0][0]:
        node_identifier = public_key
        conn.commit()
        conn.close()
        return "Success", 200
    else:
        conn.commit()
        conn.close()
        return "User not found!", 400


@app.route('/amount', methods=['GET'])
def get_amount():
    conn = sqlite3.connect("/home/alex/PycharmProjects/MeterejiCoin/Databases/Addresses")
    c = conn.cursor()
    amount = c.execute("""SELECT amount FROM tbl1 WHERE private_key=?""", (node_identifier,)).fetchone()[0]
    response = {
        'node' : node_identifier,
        'amount': amount
    }
    return jsonify(response), 200


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-p', '--port', default=5000, type=int, help='port to listen on')
    args = parser.parse_args()
    port = args.port

    app.run(host='127.0.0.1', port=port)
