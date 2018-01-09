class Block(object):
    def __init__(self, index, timestamp, transactions, proof, previousHash):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions
        self.proof = proof
        self.previousHash = previousHash
