
import hashlib
import json
import os


from nacl.encoding import HexEncoder
from nacl.signing import SigningKey


class User:
    def __init__(self, name):
        self.name = name
        self.sk = SigningKey.generate()
        self.vk = self.sk.verify_key.encode(encoder=HexEncoder).decode('utf-8')


class TransactionInput:
    def __init__(self, tx_number, value, pubkey):
        self.tx_number = tx_number
        self.value = value
        self.pubkey = pubkey


class TransactionOutput:
    def __init__(self, value, pubkey):
        self.value = value
        self.pubkey = pubkey


class Transaction:
    def __init__(self, inputs, number, outputs, sig):
        self.inputs = inputs
        self.number = number
        self.outputs = outputs
        self.sig = sig


def generate_hash(secrets):
    dk = hashlib.sha256()
    dk.update(b''.join(s.encode() for s in secrets))
    return dk.hexdigest()


def generateTransaction(senders, send_tx_numbers, receivers, values_sent, values_received, genesis):
    inputs = [TransactionInput(tx_number=n, value=v, pubkey=s.vk) for (n, v, s) in zip(send_tx_numbers, values_sent, senders)]
    outputs = [TransactionOutput(value=v, pubkey=r.vk) for (v, r) in zip(values_received, receivers)]

    if genesis:
        user = User("Genesis")
        user.vk = receivers[0].vk
        signature = generateSignature(json.dumps(inputs), json.dumps(outputs), user)
    else:
        signature = generateSignature(json.dumps(inputs), json.dumps(outputs), senders[0])
    concatSig = signature.signature + signature.message
    number = generate_hash([json.dumps(inputs), json.dumps(outputs), concatSig])

    return Transaction(inputs, number, outputs, concatSig.decode('utf-8'))



def generateSignature(input, output, user):
    temp = input.encode('utf-8')
    temp += output.encode('utf-8')
    signature = user.sk.sign(temp, encoder=HexEncoder)
    return signature


def buildJsonTransaction(tx):
    fullTx = (
        '{"number":"' + str(tx.number) + '", "inputs": [' + str(json.dumps(tx.inputs, default=lambda x: x.__dict__)[1:-1])
        + '], "outputs": [' + str(json.dumps(tx.outputs, default=lambda x: x.__dict__)[1:-1]) + '], "sig": "' + str(tx.sig)
        + '"},'
    )
    return fullTx




def generateTransactionList(users, outFilename):
    script_dir = os.path.dirname(__file__)  # <-- absolute dir the script is in
    abs_file_path = os.path.join(script_dir, outFilename)

    f = open(abs_file_path, "w")
    f.write("[\n")
    # genesis block/transaction
    genesisBlock = generateTransaction([], [], [users[0]], [], [100], True)
    print(buildJsonTransaction(genesisBlock), file=f)

    # all other transactions
    tx1 = generateTransaction([users[0]], [genesisBlock.number],
                              [users[0], users[1]], [100], [70, 30], False)  # Bob is paying Alice 30
    print(buildJsonTransaction(tx1), file=f)

    tx2 = generateTransaction([users[0]], [tx1.number],
                              [users[0], users[2]], [70], [40, 30], False)  # Bob is paying Steve 30
    print(buildJsonTransaction(tx2), file=f)

    tx3 = generateTransaction([users[2]], [tx2.number],
                              [users[2], users[3]], [30], [20, 10], False)  # Steve is paying Phil 10
    print(buildJsonTransaction(tx3), file=f)
    
    malTx1 = generateTransaction([users[6]], [tx1.number],
                                 [users[6], users[7]], [10], [5, 5], False)  # BAD TX: Stacy (no coins) paying Candice 5
    print(buildJsonTransaction(malTx1), file=f)

    tx4 = generateTransaction([users[0]], [tx2.number],
                              [users[0], users[5]], [40], [25, 15], False)  # Bob is paying John 15
    print(buildJsonTransaction(tx4), file=f)

    tx5 = generateTransaction([users[1]], [tx1.number],
                              [users[1], users[4]], [30], [15, 15], False)  # Alice is paying Barbara 15
    print(buildJsonTransaction(tx5), file=f)

    tx6 = generateTransaction([users[2]], [tx3.number],
                              [users[2], users[6]], [20], [15, 5], False)  # Steve is paying Stacy 5
    print(buildJsonTransaction(tx6), file=f)

    malTx2 = generateTransaction([users[6]], ['0'],
                                   [users[6], users[7]], [10], [5, 5], False)  # BAD TX: Invalid input transaction number
    print(buildJsonTransaction(malTx2), file=f)

    tx7 = generateTransaction([users[0]], [tx4.number],
                              [users[0], users[7]], [25], [15, 10], False)  # Bob paying Candice 10
    print(buildJsonTransaction(tx7), file=f)

    tx8 = generateTransaction([users[2]], [tx6.number],
                              [users[2], users[0]], [15], [10, 5], False)  # Steve is paying Bob 5
    print(buildJsonTransaction(tx8), file=f)

    tx9 = generateTransaction([users[5]], [tx4.number],
                              [users[5], users[6]], [15], [10, 5], False)  # John is paying Stacy 5
    print(buildJsonTransaction(tx9), file=f)

    malTx3 = generateTransaction([users[6]], [tx9.number],
                                 [users[6], users[7]], [10], [6, 5], False)  # BAD TX: Inputs outputs dont add up
    print(buildJsonTransaction(malTx3), file=f)

    tx10 = generateTransaction([users[4]], [tx5.number],
                               [users[4], users[3]], [15], [10, 5], False)  # Barbara is paying Phil 5
    print(buildJsonTransaction(tx10), file=f)

    tx11 = generateTransaction([users[6]], [tx6.number, tx9.number],
                               [users[4]], [5, 5], [10], False)  # Stacy is paying Barbara 10
    print(buildJsonTransaction(tx11), file=f)

    tx12 = generateTransaction([users[7]], [tx7.number],
                               [users[5]], [10], [10], False)  # Candice is paying John 10
    print(buildJsonTransaction(tx12), file=f)

    malTx4 = generateTransaction([users[7]], [tx7.number],
                                 [users[6]], [10], [10], False)  # BAD TX: Candice trying to double spend
    print(buildJsonTransaction(malTx4), file=f)

    
    tx13 = generateTransaction([users[5]], [tx9.number, tx12.number],
                           [users[2]], [10, 10], [20], False)  # John is paying Steve 20
    print(buildJsonTransaction(tx13), file=f)

    
    
    tx14 = generateTransaction([users[4]], [tx10.number, tx11.number],
                               [users[1]], [10, 10], [20], False)  # Barbara is paying Alice 20
    print(buildJsonTransaction(tx14), file=f)

    tx15 = generateTransaction([users[2]], [tx8.number, tx13.number],
                               [users[2], users[0]], [10, 20], [15, 15], False)  # Steve is paying Bob 15
    print(buildJsonTransaction(tx15), file=f)

    f.write("]")
    f.close()
    return genesisBlock




def main(file_name):
    names = ['Bob', 'Alice', 'Steve', 'Phil', 'Barbara', 'John', 'Stacy', 'Candice']
    users = []

    # make

    for n in names:
        users.append(User(n))

    generateTransactionList(users,  file_name)


if __name__ == "__main__":
    main("output/transactions.json")
