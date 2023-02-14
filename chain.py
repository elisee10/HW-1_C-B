from txGenerator import generate_hash
from Transaction import Transaction
from block import Block
import copy

class Chain:
    def __init__(self, genesisBlock: Block):
        self.blocks = [genesisBlock]
        self.unspentCoin2BlockIdx = {}
        for output in genesisBlock.tx.output:
            key = generate_hash([genesisBlock.tx.number.encode("utf-8"),output['pubkey'].encode("utf-8")])
            self.unspentCoin2BlockIdx[key] = 0

    def add_block(self, tx: Transaction):
        last_block_hash = self.blocks[-1].hash()
        new_block = Block(tx, last_block_hash)
        self.unspentCoin2BlockIdx = self.validate_block(new_block)
        self.blocks.append(new_block)
        return True

    def validate_block(self, new_block: Block):
        new_unspentCoin2BlockIdx = copy.deepcopy(self.unspentCoin2BlockIdx)
        new_tx = new_block.tx

        sender_pk = new_tx.input[0]['output']['pubkey']
        for next_tx_input in new_tx.input:
            new_tx_input_num = next_tx_input['number']
            key = generate_hash([new_tx_input_num.encode('utf-8'), sender_pk.encode('utf-8')])

            if key not in self.unspentCoin2BlockIdx:
                raise Exception("Double Spend Attempted ")
            claimed_block_index = self.unspentCoin2BlockIdx[key]
            claimed_block = self.blocks[claimed_block_index]

            claimed_tx_outputs = claimed_block.tx.output
            found_output = False
            for output in claimed_tx_outputs:
                if output['pubkey'] == next_tx_input['output']['pubkey'] and output['value'] == next_tx_input['output']['value']:
                    found_output = True
            if not found_output:
                raise Exception(f"user {next_tx_input['pubkey']} tried to spend an output that was not theirs")

            del new_unspentCoin2BlockIdx[key]

        for output in new_block.tx.output:
            reciever_key = output['pubkey']
            new_key = generate_hash([new_tx.number.encode("utf-8"), reciever_key.encode("utf-8")])
            new_unspentCoin2BlockIdx[new_key] = len(self.blocks)
        return new_unspentCoin2BlockIdx
            
                
    def validate_chain(blocks, genesis_block):
        try:
            if blocks[0].hash() != genesis_block.hash():
                return False
            built_blocks = [genesis_block]
            unspent_coin_2_block_index = {}
            for block in blocks[1:]:
                if block.pow < 0x07FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF:
                    unspent_coin_2_block_index = Chain.validate_block(
                        built_blocks, block, unspent_coin_2_block_index
                    )
                    if not unspent_coin_2_block_index:
                        raise Exception("Invalid Block")
                    built_blocks.append(block)
            return True
        except:
            return False

    def as_string(self, as_tx=False):
        result = "[\n"
        for i, block in enumerate(self.blocks):
            if as_tx:
                result += block.as_tx()
            else:
                result += block.as_block()
            result += ",\n"

        return result[:-2] + "\n]\n"

