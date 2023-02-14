import hashlib
import json
import random
import sys
import threading
import time
import copy
import queue
import os
import shutil


from block import Block
from chain import Chain
from Transaction import Transaction

class HonestNode(threading.Thread):
    def __init__(self, name, genesis_block):
        super().__init__()
        self.name = name
        self.q = queue.Queue()
        self.invalid_tx = set()
        self.unverifiable_tx = set()
        self.tx_in_chain = set()
        self.chain = Chain(genesis_block)

    def run(self):
        print(f"{self.name} running...")
        while not stop_threads:
            while not self.q.empty():
                self.receive_chain()
            self.process_unverified_tx()
        print(f"{self.name} stopped")

    def process_unverified_tx(self):
        for tx_num, unverified_tx in list(unverified_txs.items()):
            if tx_num not in self.tx_in_chain and tx_num not in self.invalid_tx and tx_num not in self.unverifiable_tx:
                try:
                    tx = Transaction(unverified_tx)
                except:
                    self.invalid_tx.add(tx_num)
                    break
                try:
                    self.chain.add_tx(tx)
                    self.tx_in_chain.add(tx.number)
                    self.unverifiable_tx = set()
                    self.broadcast_chain()
                except:
                    self.unverifiable_tx.add(tx_num)
                    break

    def send_chain(self, chain):
        self.q.put(chain)

    def receive_chain(self):
        new_chain = self.q.get()
        if len(new_chain.blocks) >= len(self.chain.blocks):
            if Chain.validate_chain(new_chain, self.chain.blocks[0]):
                self.unverifiable_tx = set()
                self.tx_in_chain = set()
                self.chain = copy.deepcopy(new_chain)
                for block in self.chain.blocks:
                    self.tx_in_chain.add(block.tx.number)

    def broadcast_chain(self):
        print(f"{self.name} broadcasting chain")
        for node_key, node in nodes.items():
            if node_key != self.name:
                node.send_chain(self.chain)

    def write_to_file(self, file_name):
        with open(f"output/{file_name}.json", 'w') as outfile:
            outfile.write(self.chain.as_string(as_tx=True))
            outfile.close()

    def write_blockchain_to_file(self, file_name):
        with open(f"output/{file_name}.json", 'w') as outfile:
            outfile.write(self.chain.as_string())
            outfile.close()



class MaliciousNode(threading.Thread):
    def __init__(self, name, genesisBlock, q, stop_threads):
        super().__init__()
        self.name = name
        self.q = q
        self.chain = Chain(genesisBlock)
        self.badBlocks = [RandomBlock, MissingNonceBlock, MissingPowBlock, MissingPrevBlock, MissingTxBlock]
        self._stop_threads = stop_threads

    def run(self):
        try:
            print(self.name + " running...")
            while True:
                time.sleep(1)
                while not self.q.empty():
                    if self._stop_threads.is_set():
                        break
                    self.receive_chain()
                if self._stop_threads.is_set():
                    break
        finally:
            print(self.name + " stopped")

    def send_chain(self, chain):
        self.q.put(chain)

    def receive_chain(self):
        new_chain = self.q.get()
        if len(new_chain.blocks) >= len(self.chain.blocks):
            new_chain = copy.deepcopy(new_chain)
            blocks  = new_chain.blocks
            num_blocks_to_add = 3
            for i in range(num_blocks_to_add):
                bad_block_class = random.choice(self.badBlocks)
                blocks.append(bad_block_class())
            self.broadcast_chain(new_chain)

    def broadcast_chain(self, chain):
        print(self.name + " broadcasting chain ")
        for node_key, node in nodes.items():
            if node_key != self.name:
                node.send_chain(chain)

def generate_nonce(length):
    """Generate pseudorandom number."""
    return ''.join([str(random.randint(0, 9)) for i in range(length)])

class RandomBlock():
    def __init__(self):
        self.tx = generate_nonce(64)
        self.prev = generate_nonce(64)
        self.nonce = generate_nonce(64)
        self.pow = generate_nonce(128)

class MissingTxBlock():
    def __init__(self):
        self.prev = generate_nonce(64)
        self.nonce = generate_nonce(64)
        self.pow = generate_nonce(128)

class MissingPrevBlock():
    def __init__(self):
        self.tx = generate_nonce(64)
        self.nonce = generate_nonce(64)
        self.pow = generate_nonce(128)

class MissingNonceBlock():
    def __init__(self):
        self.tx = generate_nonce(64)
        self.prev = generate_nonce(64)
        self.pow = generate_nonce(128)

class MissingPowBlock():
    def __init__(self):
        self.tx = generate_nonce(64)
        self.prev = generate_nonce(64)
        self.nonce = generate_nonce(64)
        self.pow = generate_nonce(128)
        
        

# Global variables
stop_threads = False
nodes = {}
unverified_txs = {}
STOP_LENGTH_CHAIN = 16

def run_simulation(txs, num_honest_nodes, num_malicious_nodes, genesis_block):
    honest_nodes_left_to_finish = start_nodes(num_honest_nodes, num_malicious_nodes, genesis_block)
    # Add transactions, which causes nodes to process them
    for tx in txs:
        random_sleep_time = random.uniform(0, 1)
        time.sleep(random_sleep_time)
        unverified_txs[tx['number']] = tx
        
    while True:
        if len(honest_nodes_left_to_finish) == 0:
            # Put in an order to stop all nodes
            global stop_threads
            stop_threads = True
            break
        else:
            to_remove = False
            for honest_node_id in honest_nodes_left_to_finish:
                honest_node = nodes[honest_node_id]
                if len(honest_node.chain.blocks) >= STOP_LENGTH_CHAIN:
                    to_remove = honest_node_id
                    break
            
            if to_remove:
                nodes[to_remove].print()
                if to_remove == "Node0":
                    nodes[to_remove].print_block_chain()
                honest_nodes_left_to_finish.remove(to_remove)
    
    # Wait for all nodes to stop
    for node in nodes.values():
        node.join()
    print('All done!')

def id_to_key(idx):
    return 'Node' + str(idx)

def start_nodes(num_honest, num_malicious, genesis_block):
    global nodes
    honest_node_ids = set()
    for i in range(num_honest):
        key = id_to_key(i)
        honest_node_ids.add(key)
        nodes[key] = HonestNode(key, genesis_block)
        nodes[key].start()
    
    for i in range(num_malicious):
        key = id_to_key(num_honest + i)
        nodes[key] = MaliciousNode(key, genesis_block)
        nodes[key].start()
    return honest_node_ids

def set_up_txs(file_name):
    return txGenerator.main(file_name)



if __name__ == "__main__":
    # validate user input
    if len(sys.argv) < 2:
        print("ERROR: you must specify a path to your input JSON file")
        sys.exit(1)

    file_name = sys.argv[1]
    genesis_block = Block(setupTxs(file_name), "")

    with open(file_name) as json_file:
        txs = json.load(json_file)

    NUM_HONEST_NODES = 5
    NUM_MALICIOUS_NODES = 1
    run_simulation(txs, NUM_HONEST_NODES, NUM_MALICIOUS_NODES, genesis_block)
    