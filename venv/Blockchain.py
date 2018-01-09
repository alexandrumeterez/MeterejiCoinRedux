import hashlib
import json
from time import time
import Block
import Transaction
from urllib.parse import urlparse
import requests


class Blockchain(object):
    difficulty = 2

    def __init__(self):
        self.chain = []
        self.transactions = []
        self.nodes = set()  # People(nodes) in the network
        self.new_block(previous_hash='1')
        self.proof_of_work(self.chain[0])

    def new_block(self, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.transactions,
            'nonce': 0,
            'previous_hash': previous_hash,
            'block_hash': None
        }

        # Reset the current list of transactions
        self.transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        self.transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        block_string = str(block['previous_hash']) + str(block['nonce'])
        return hashlib.sha256(block_string.encode()).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, block):
        nonce = 0
        while self.valid_proof(block) is False:
            nonce += 1
            block['nonce'] = nonce
        block['block_hash'] = Blockchain.hash(block)
        return nonce

    @staticmethod
    def valid_proof(block):
        return Blockchain.hash(block)[:Blockchain.difficulty] == "00"

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    @staticmethod
    def valid_chain(chain):
        index = 1
        last_block = chain[0]
        while index < len(chain):
            block = chain[index]
            # Check if current hash and previous hash match
            if block['previous_hash'] != last_block['block_hash']:
                return False

            # Check if current hash is correct
            if block['block_hash'] != Blockchain.hash(block):
                return False

            last_block = block
            index += 1
        return True

    def resolve_conflict(self):
        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        # Check ledges of all nodes in the network
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:  # On success
                length = response.json()['length']
                chain = response.json()['chain']

                # Consensus: longest chain replaces current chain if needed
                if length > max_length and Blockchain.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain too if needed
        if new_chain:
            self.chain = new_chain
            return True
        return False
