# coding: UTF-8
import hashlib
import json
import sys
from time import time
from uuid import uuid4
from textwrap import dedent
from flask import Flask, jsonify, request
from urllib.parse import urlparse
import requests

args = sys.argv

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.difficulty = "0000"
        self.nodes = set()
        # ジェネシスブロックを作る
        self.new_block(previous_hash=1, nonce=0, merkle_root_hash=1)

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)


    def new_block(self, nonce=0, previous_hash=None, merkle_root_hash=None):
        # 新しいブロックを作り、チェーンに加える
        """
        ブロックチェーンに新しいブロックを作る
        :param previous_hash: (オプション) <str> 前のブロックのハッシュ
        :param merkle_root_hash: <str> トランザクションのマークルルートハッシュ
        :return: <dict> 新しいブロック
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'nonce': nonce,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
            'merkle_root_hash': merkle_root_hash or self.merkle_root(self.current_transactions)
        }

        block['nonce'] = self.proof_of_work(block)
        self.chain.append(block)
        # 現在のトランザクションリストをリセット
        self.current_transactions = []

        return block

    @staticmethod
    def dhash(data):
        encoded_data = data.encode()
        hash_data = str(hashlib.sha256(encoded_data).hexdigest()).encode()
        return hashlib.sha256(hash_data).hexdigest()

    @staticmethod
    def extract_txid(nodes):
        if nodes[0].__class__.__name__ == "dict":
            txid_nodes = []
            for node in nodes:
                txid_nodes.append(node['txid'])
            return txid_nodes
        else:
            return nodes


    def merkle_root(self, nodes):
        nodes = self.extract_txid(nodes)
        print("----------")
        print("the number of tx")
        print(len(nodes))
        print("----------")

        if len(nodes) == 1:
            if len(self.current_transactions) == 1:
                mRoot = self.dhash(nodes[0])
            else:
                mRoot = nodes[0]
            return mRoot
        else:
            upper_nodes = []
            for x in range(0, len(nodes), 2):
                if len(nodes) % 2 != 0 and x == (len(nodes)-1):
                    join_nodes = str(nodes[x]) + str(nodes[x])
                    upper_nodes.append(self.dhash(join_nodes))
                else:
                    join_nodes = str(nodes[x]) + str(nodes[x+1])
                    upper_nodes.append(self.dhash(join_nodes))
            print(upper_nodes)
            return self.merkle_root(upper_nodes)


    def new_transaction(self, sender, recipient, amount, transaction_id):
        # 新しいトランザクションをリストに加える
        """
        次に採掘されるブロックに加える新しいトランザクションを作る
        :param sender: <str> 送信者のアドレス
        :param recipient: <str> 受信者のアドレス
        :param amount: <int> 量
        :return: <int> このトランザクションを含むブロックのアドレス
        """

        transaction = {
            'txid': transaction_id,
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        }

        transaction['txid'] = self.hash(transaction)

        self.current_transactions.append(transaction)

        return self.last_block['index'] + 1

    @property
    def last_block(self):
        # チェーンの最後のブロックをリターンする
        return self.chain[-1]

    @staticmethod
    def hash(block):
        # ブロックをハッシュ化する
        """
        ブロックの SHA-256 ハッシュを作る
        :param block: <dict> ブロック
        :return: <str>
        """

        # 必ずディクショナリ（辞書型のオブジェクト）がソートされている必要がある。そうでないと、一貫性のないハッシュとなってしまう
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()



    def proof_of_work(self, block):
        nonce = 0
        while self.valid_proof(block, nonce) is False:
            nonce += 1

        return nonce

    def change_difficulty(self):
        recent_blocks = blockchain.chain[-5:]
        if len(recent_blocks) < 5:
            return 'Missing 5 blocks', 400
        i = 0
        recent_generate_blocktime = 0
        while i < 4:
            recent_generate_blocktime += (recent_blocks[i+1]['timestamp'] - recent_blocks[i]['timestamp'])
            i += 1
        average_time = recent_generate_blocktime / (len(recent_blocks) - 1)

        if average_time > 10:
            self.difficulty = self.difficulty[1:]
        elif average_time < 10:
            self.difficulty += "0"

        print("\n----------------\n")
        print("Ajust difficulty...\n")
        print(f'Now difficulty is {blockchain.difficulty}')
        print("\n----------------\n")
        return blockchain.difficulty


    def valid_proof(self, block, nonce):
        """
        プルーフが正しいかを確認する: hash(last_proof, proof)の最初の4つが0となっているか？
        :param last_proof: <int> 前のプルーフ
        :param proof: <int> 現在のプルーフ
        :return: <bool> 正しければ true 、そうでなれけば false
        """
        block['nonce'] = nonce
        guess_hash = self.hash(block)

        return guess_hash[:len(self.difficulty)] == self.difficulty

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n---------------\n")

            if block['previous_hash'] != self.hash(last_block):
                return False

            if not self.valid_proof(block, block['nonce']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None

        max_length = len(self.chain)

        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        if new_chain:
            self.chain = new_chain
            return True

        return False




app = Flask(__name__)

# このノードのグローバルにユニークなアドレスを作る
node_identifire = str(uuid4()).replace('-', '')

# ブロックチェーンクラスをインスタンス化する
blockchain = Blockchain()

@app.route('/transactions/new', methods=['POST'])
def new_transactions():
    values = request.get_json()
    # POSTされたデータに必要なデータがあるかを確認
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # 新しいトランザクションを作る
    txid = len(blockchain.current_transactions) + 1
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'], txid)

    response = {'message': f'トランザクションはブロック{index}に追加されました'}
    return jsonify(response), 201


# メソッドはGETで/mineエンドポイントを作る
@app.route('/mine', methods=['GET'])
def mine():

    # コインベーストランザクション
    # プルーフを見つけたことに対する報酬を得る
    # 送信者は、採掘者が新しいコインを採掘したことを表すために"0"とする
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifire,
        amount=1,
        transaction_id="0"
    )

    # チェーンに新しいブロックを加えることで、新しいブロックを採掘する
    block = blockchain.new_block()


    last_block = blockchain.last_block
    if last_block['index'] % 5 == 0:
        blockchain.change_difficulty()

    response = {
        'message': '新しいブロックを採掘しました',
        'index': block['index'],
        'transactions': block['transactions'],
        'nonce': block['nonce'],
        'timestamp': block['timestamp'],
        'previous_hash': block['previous_hash'],
        'merkle_root_hash': block['merkle_root_hash']
    }
    return jsonify(response), 200

# メソッドはGETで、フルのブロックチェーンをリターンする/chainエンドポイントを作る
@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/difficulty', methods=['GET'])
def now_difficulty():
    response = {
        'difficulty': blockchain.difficulty
    }

    return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_node():
    values = request.get_json()

    nodes = values.get('nodes')
    if nodes is None:
        return "Error: 有効ではないノードのリストです", 400

    for node in nodes:
        blockchain.register_node(node)

    response = {
        'message': '新しいノードが追加されました',
        'total_nodes': list(blockchain.nodes),
    }

    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'チェーンが置き換えられました',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'チェーンが確認されました',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


# port5000でサーバーを起動する
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=args[1])
