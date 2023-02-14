import json
from typing import List, Dict
import nacl.signing
import nacl.encoding
from txGenerator import generate_hash, generateSignature


class Transaction:
    def __init__(self, tx: Dict):
        self.input = tx['input']
        self.number = tx['number']
        self.output = tx['output']
        self.sig = tx['sig']
        self.validate()

    def net_tx(self) -> Dict:
        net = {}
        for i in self.input:
            output = i['output']
            sender_pk = output['pubkey']
            send_amount = output['value']
            if sender_pk not in net:
                net[sender_pk] = 0
            net[sender_pk] -= send_amount
        for o in self.output:
            receiver_pk = o['pubkey']
            receive_amount = o['value']
            if receiver_pk not in net:
                net[receiver_pk] = 0
            net[receiver_pk] += receive_amount
        return net

    def validate(self):
        if not all([self.input, self.output, self.sig, self.number]):
            raise Exception("Transaction is missing required fields")

        hex_hash = generate_hash(
            [
                json.dumps(self.input).encode('utf-8'),
                json.dumps(self.output).encode('utf-8'),
                self.sig.encode('utf-8')
            ]
        )
        if self.number != hex_hash:
            raise Exception("Transaction number does not match generated hash")

        total_in_out = sum(self.net_tx().values())
        if total_in_out != 0:
            raise Exception("Input and output amounts do not match")

        vk = nacl.signing.VerifyKey(self.input[0]['output']['pubkey'], encoder=nacl.encoding.HexEncoder)
        try:
            vk.verify(self.sig, encoder=nacl.encoding.HexEncoder)
        except nacl.exceptions.BadSignatureError:
            raise Exception("Transaction signature is invalid")
