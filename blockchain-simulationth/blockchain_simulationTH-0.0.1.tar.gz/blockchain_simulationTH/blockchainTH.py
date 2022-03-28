# -*- coding: utf-8 -*-
#import libraries
from hashlib import sha256
import random 
import datetime
import binascii
from time import ctime

from io import *
from ecc import *
from helper import *
 
from script import *


tx = {}
#tx[self.name] = self.tx_coinbase
txid = {}
#txid['name'] = tx.id() 
find_amount = {}
#find[tx.id()]= [target_amount]
find_scriptpub = {}
#find[tx.id()]= [script_pubkey]
find_user = {}
#find_user['name'] = [sender,receiver]

#mempool transaction
mempool_tx = []

#UTXO
utxo = []

##########################Client######################################
class Client:
    def __init__(self,name):
        self.name = name
        self.balance = 0
        private_key = random.getrandbits(256)
        self.private_key = PrivateKey(private_key)
        self.private_key_wif = self.private_key.wif(testnet=True)
        self.public_key = self.private_key.point
        self.address = self.private_key.point.address(testnet=True)
        print('------------------------------------------------------------------')
        print('                         สร้างผู้ใช้ {} สำเร็จ!!!'.format(self.name))
        print('------------------------------------------------------------------')
        #print('###########รายละเอียดของผู้ใช้ {}############\n'.format(self.name))
        print('กุญแจส่วนตัวของผู้ใช้ {} ------> {}'.format(self.name,self.private_key))
        print('กุญแจสาธารณะของผู้ใช้ {} ---> {}'.format(self.name,self.public_key))
        print('เลขที่บัญชีของผู้ใช้ {} ----------> {}\n'.format(self.name,self.address))

    def __repr__(self):
         return '---------------------------------\n\
Information of {} \n\
---------------------------------\n\
Private key: {}\n\nPublic key: {}\\n\nAddress: {}\n\n\
-------------------------------------------------------------------------'\
        .format(self.name,self.private_key,self.public_key,self.address)
     
    def deposit(self,amount):
        self.balance = self.balance + amount


    def withdraw(self,amount):
        if(self.balance < amount):
            result = 'unbalance'
        else:
            self.balance = self.balance - amount
            result = 'balance'
        return result

    def view_balance(self):
        print('===Personal Details===')
        print('Name :',self.name)
        print( 'เงินในบัญชีของ {} เท่ากับ {}'.format(self.name,self.balance))
        print()

#########################################################################################


#####################################Transaction#########################################
class Coinbase:
    def __init__(self,name,receiver,amount):
        self.name = name
        self.version = 1
        self.locktime = 0
        
        #Tx_In
        self.tx_ins = []
        
        prev_tx = bytes.fromhex('0000000000000000000000000000000000000000000000000000000000000000')
        prev_index = int(0xffffffff)
        
        extradata = b'This is Coinbase'
        sig = len(extradata).to_bytes(2, 'big') + extradata
        script_sig = Script([sig])
        
        self.tx_ins.append(TxIn(prev_tx,prev_index,script_sig))

        #Tx_Out
        self.tx_outs = []
        
        target_amount = int(amount*1000000)
        target_address = receiver.address
        target_h160 = decode_base58(receiver.address)
        script_pubkey = p2pkh_script(target_h160)
        
        self.tx_outs.append(TxOut(target_amount, script_pubkey))

        

        find_user[self.name] = ['',receiver]
        find_amount[self.name]= [target_amount,0]
        find_scriptpub[self.name] = [script_pubkey,0]
        txid[self.name] = self.id()
        tx[self.name] = self
        
        print('------------------------------------------------------------------')
        print('     สร้าง Coinbase Transaction : {} สำเร็จ!!!'.format(self.name))
        print('------------------------------------------------------------------')
        tx_ins = ''
        for tx_in in self.tx_ins:
                tx_ins += tx_in.__repr__() 
        tx_outs = ''
        for tx_out in self.tx_outs:
                tx_outs += tx_out.__repr__() 
        print('txid : {}'.format(self.id()))
        print('version : {}'.format( self.version))
        print('input : {}'.format(tx_ins))
        print('output : {}'.format(tx_outs))
        print('locktime : {}\n'.format(self.locktime))

    def __repr__(self):
            tx_ins = ''
            for tx_in in self.tx_ins:
                tx_ins += tx_in.__repr__() + '\n'
            tx_outs = ''
            for tx_out in self.tx_outs:
                tx_outs += tx_out.__repr__() + '\n'
            return 'tx: {}\nversion: {}\ntx_ins: {}tx_outs: {}locktime: {}\n'.format(
                self.id(),
                self.version,
                tx_ins,
                tx_outs,
                self.locktime,
            )
        
    def id(self):
            return self.hash().hex()

    def hash(self):
            return hash256(self.serialize())[::-1]
        
    def serialize(self):
            result = int_to_little_endian(self.version, 4)
            result += encode_varint(len(self.tx_ins))
            for tx_in in self.tx_ins:
                result += tx_in.serialize()
            result += encode_varint(len(self.tx_outs))
            for tx_out in self.tx_outs:
                 result += tx_out.serialize()
            result += int_to_little_endian(self.locktime, 4)
            return result

class Transaction:
    def __init__(self,txname,sender,receiver,value,fromtx,index):
        self.name = txname
        self.sender = sender
        self.receiver = receiver
        self.value = value
        self.fromtx = fromtx
        self.index = index
        #Version
        self.version = 1
        
        #TxIn
        self.tx_ins = []
        prev_tx = bytes.fromhex(txid[fromtx] )
        prev_index = index
        self.tx_ins.append(TxIn(prev_tx,prev_index))

        #TxOut
        self.tx_outs = []
        self.target_amount = int(value*1000000)
        target_address = receiver.address
        target_h160 = decode_base58(receiver.address)
        script_pubkey_target = p2pkh_script(target_h160)
        self.tx_outs.append(TxOut(self.target_amount, script_pubkey_target))

        amount = find_amount[fromtx][index]-int(value*1000000)
        self.back_amount = int(amount)
        back_address = sender.address
        back_h160 = decode_base58(sender.address)
        script_pubkey_back = p2pkh_script(back_h160)
        self.tx_outs.append(TxOut(self.back_amount, script_pubkey_back))

        #Locktime
        self.locktime = 0
        
        #Tx ไม่ต้องมี รวมกันได้
        #self.tx = Tx(1,self.tx_ins,self.tx_outs,0,True)

        find_user[self.name] = [self.sender,self.receiver]
        find_amount[self.name]= [self.back_amount,self.target_amount]
        find_scriptpub[self.name] = [script_pubkey_back,script_pubkey_target]
        txid[self.name] = self.id()
        global tx
        tx[self.name] = self

        #sig_hash
        s = int_to_little_endian(self.version, 4)
        s += encode_varint(len(self.tx_ins))
        ############################################################
        change_h160 = decode_base58(sender.address)
        script_pubkey = p2pkh_script(change_h160)
        script_sig = script_pubkey
        
        s += TxIn(prev_tx = self.tx_ins[0].prev_tx,
                  prev_index=self.tx_ins[0].prev_index,
                  script_sig=script_sig,
                  sequence=self.tx_ins[0].sequence,).serialize()
        ############################################################
        s += encode_varint(len(self.tx_outs))
        for tx_out in self.tx_outs:
            s += tx_out.serialize()
        s += int_to_little_endian(self.locktime, 4)
        s += int_to_little_endian(SIGHASH_ALL, 4)
        sig_hash = hash256(s)
        self.z = int.from_bytes(sig_hash, 'big')
        
        der = sender.private_key.sign(self.z).der()
        sig = der + SIGHASH_ALL.to_bytes(1,'big')
        sec = sender.private_key.point.sec()
        self.script_sig = Script([sig,sec])
        
        self.tx_ins[0].script_sig = self.script_sig

        print('------------------------------------------------------------------')
        print('     สร้าง  Transaction : {} สำเร็จ!!!'.format(self.name))
        print('------------------------------------------------------------------')
        tx_ins = ''
        for tx_in in self.tx_ins:
                tx_ins += tx_in.__repr__() 
        tx_outs = ''
        for tx_out in self.tx_outs:
                tx_outs += tx_out.__repr__() 
        print('txid : {}'.format(self.id()))
        print('version : {}'.format( self.version))
        print('input : {}'.format(tx_ins))
        print('output : {}'.format(tx_outs))
        print('locktime : {}\n'.format(self.locktime))
        
        #Evaluate Transaction
        #script_pubkey = Script([0xac])
        script_pubkey =  find_scriptpub[self.fromtx][self.index]
        script_sig = self.script_sig
        combined_script = script_sig + script_pubkey
        #Evaluate fee
        input_sum, output_sum = 0, 0
        input_sum = find_amount[self.fromtx][self.index]
        
        output_sum = self.target_amount + self.back_amount
       
        
        
        
        if    input_sum - output_sum >= 0:
            #print('Transaction Evaluate fee: Pass')
            #Evaluate Script
            if combined_script.evaluate(self.z) == True:
                #print('Transaction Evaluate script: Pass')
                #print('Transaction Add Transaction to block')
                self.txverify = True
            else:
                #print('Transaction1 Evaluate script: Fail')
                self.txverify = False
        else:
            #print('Not add Transaction1 to block')
            self.txverify = False
        
        
    def __repr__(self):
        tx_ins = ''
        for tx_in in self.tx_ins:
            tx_ins += tx_in.__repr__() + '\n'
        tx_outs = ''
        for tx_out in self.tx_outs:
            tx_outs += tx_out.__repr__() + '\n'
        return 'tx: {}\nversion: {}\ntx_ins:{}tx_outs:{}locktime: {}\n'.format(
            self.id(),
            self.version,
            tx_ins,
            tx_outs,
            self.locktime,
        )
    def id(self):
        return self.hash().hex()

    def hash(self):
        return hash256(self.serialize())[::-1]

    def serialize(self):
        result = int_to_little_endian(self.version, 4)
        result += encode_varint(len(self.tx_ins))
        for tx_in in self.tx_ins:
            result += tx_in.serialize()
        result += encode_varint(len(self.tx_outs))
        for tx_out in self.tx_outs:
            result += tx_out.serialize()
        result += int_to_little_endian(self.locktime, 4)
        return result

    def fee(self):
        input_sum, output_sum = 0, 0
        for tx_in in self.tx_ins:
            input_sum += tx_in.value(self.testnet)
        for tx_out in self.tx_outs:
            output_sum += tx_out.amount
        return input_sum - output_sum
        
class TxIn:
    def __init__(self, prev_tx, prev_index, script_sig=None, sequence=0xffffffff):
        self.prev_tx = prev_tx
        self.prev_index = prev_index
        if script_sig is None:
            self.script_sig = Script()
        else:
            self.script_sig = script_sig
        self.sequence = sequence

    def __repr__(self):
        return '\n   Previous transaction ID: {}\n   Previous transaction index: {}\n   ScriptSig: {}\n   sequence: {}'.format(
            self.prev_tx.hex(),
            self.prev_index,
            self.script_sig,
            self.sequence
        )

    def serialize(self):
        result = self.prev_tx[::-1]
        result += int_to_little_endian(self.prev_index, 4)
        result += self.script_sig.serialize()
        result += int_to_little_endian(self.sequence, 4)
        return result


class TxOut:

    def __init__(self, amount, script_pubkey):
        self.amount = amount
        self.script_pubkey = script_pubkey

    def __repr__(self):
        return '\n   Amount: {}\n   ScriptPub: {}'.format(self.amount, self.script_pubkey)

    def serialize(self):
        result = int_to_little_endian(self.amount, 8)
        result += self.script_pubkey.serialize()
        return result

################################################################################
#blockchain
blockchain = []

last_block_hash = []

###############################Block############################################
class Genesisblock:
    def __init__(self,name1,name2,name3):
            self.type = 'Genesis'
            self.name1 = name1
            self.name2 = name2
            self.name3 = name3
            self.version = 2
            last_block_hash = 0
            self.prev_block = last_block_hash.to_bytes(32,'little')
            self.verified_transaction = []
            self.tx1 = tx[name1]
            self.tx2 = tx[name2]
            self.tx3 = tx[name3]
            self.verified_transaction.append(self.tx1)
            self.verified_transaction.append( self.tx2)
            self.verified_transaction.append(self.tx3)

            tx_hash1 = bytes.fromhex(tx[name1].id())
            tx_hash1_r  =  tx_hash1[::-1]
            tx_hash2 = bytes.fromhex(tx[name2].id())
            tx_hash2_r  =  tx_hash2[::-1]
            tx_hash3 = bytes.fromhex(tx[name3].id())
            tx_hash3_r  =  tx_hash3[::-1]

            tx_hash = []
            tx_hash.append(tx_hash1_r)
            tx_hash.append(tx_hash2_r)
            tx_hash.append(tx_hash3_r)
            
            self.merkle_root = merkle_root(tx_hash)[::-1]
            
            self.timestamp = int(datetime.datetime.utcnow().timestamp())
            self.bits = bytes.fromhex('1d00ffff')
            self.nonce =  ''
            
            self.block_hashes =  ''

            
            

    def __repr__(self):
           return '[\n   version: {}\n   prev_block: {}\n   merkle_root: {}\n   timestamp: {}\
\n   bits: {}\n   nonce: {}\n   verified_transaction: \n{}\n   block_hashes: {}\n]'.format(
                self.version,
                self.prev_block.hex(),
                self.merkle_root.hex(),
                ctime(time.time()),
                self.bits.hex(),    
                self.nonce,
                self.verified_transaction,
                self.block_hashes
            )
        
    def serialize(self):
            result = int_to_little_endian(self.version, 4)
            result += self.prev_block[::-1]
            result += self.merkle_root[::-1]
            result += int_to_little_endian(self.timestamp, 4)
            result += self.bits
            result += self.nonce
            return result

    def hash(self):
                s = self.serialize()
                h256 = hash256(s)
                return h256[::-1]
            
class Block:
    def __init__(self,name1,name2,name3):
        self.name1= name1
        self.name2 = name2
        self.name3 = name3
        self.type = 'Block'
        
        self.version = 2 #4 bytes
        self.prev_block = last_block_hash[-1]
        self.prev_block = bytes(last_block_hash[-1], 'utf-8') #32 bytes

        self.verified_transaction = []

        print('----------------------------------------------------------------------------')
        print('   กระบวนการตรวจสอบความถูกต้องของ Transaction')
        print('----------------------------------------------------------------------------')
        
        self.tx1 = tx[name1]
        if self.tx1.txverify == True:
            print('ธุรกรรม {} :'.format(name1))
            print('-ธุรกรรม {} มีปริมาณเงินรวมของ Input หรือธุรกรรมก่อนหน้าที่อ้างอิงถึงมากกว่าหรือเท่ากับปริมาณเงินรวมของ Output หรือปริมาณเงินรวมที่จะโอนไปให้ผู้อื่น'.format(name1))
            print('-ScriptSig ของอินพุตของธุรกรรม {} เข้าคู่กับ ScriptPubkey ของธุรกรรมที่อ้างอิงถึง '.format(name1))
            self.verified_transaction.append(self.tx1)
            print('ธุรกรรม {} มีความถูกต้อง ----> เพิ่มธุรกรรม {} เข้าไปในบล็อก\n'.format(name1,name1))
        else:
            print('ธุรกรรม {} :'.format(name1))
            print('-ธุรกรรม {} มีปริมาณเงินรวมของ Input หรือธุรกรรมก่อนหน้าที่อ้างอิงถึงน้อยกว่าหรือเท่ากับปริมาณเงินรวมของ Output หรือปริมาณเงินรวมที่จะโอนไปให้ผู้อื่น'.format(name1))
            print('-ScriptSig ของอินพุตของธุรกรรม {} ไม่เข้าคู่กับ ScriptPubkey ของธุรกรรมที่อ้างอิงถึง '.format(name1))
            print('ธุรกรรม {} มีความไม่ถูกต้อง ----> ไม่เพิ่มธุรกรรม {} เข้าไปในบล็อก\n'.format(name1,name1))
        self.tx2 = tx[name2]
        if self.tx2.txverify == True:
            print('ธุรกรรม {} :'.format(name2))
            print('-ธุรกรรม {} มีปริมาณเงินรวมของ Input หรือธุรกรรมก่อนหน้าที่อ้างอิงถึงมากกว่าหรือเท่ากับปริมาณเงินรวมของ Output หรือปริมาณเงินรวมที่จะโอนไปให้ผู้อื่น'.format(name1))
            print('-ScriptSig ของอินพุตของธุรกรรม {} เข้าคู่กับ ScriptPubkey ของธุรกรรมที่อ้างอิงถึง '.format(name2))
            self.verified_transaction.append(self.tx2)
            print('ธุรกรรม {} มีความถูกต้อง ----> เพิ่มธุรกรรม {} เข้าไปในบล็อก\n'.format(name2,name2))
        else:
            print('ธุรกรรม {} :'.format(name2))
            print('-ธุรกรรม {} มีปริมาณเงินรวมของ Input หรือธุรกรรมก่อนหน้าที่อ้างอิงถึงน้อยกว่าหรือเท่ากับปริมาณเงินรวมของ Output หรือปริมาณเงินรวมที่จะโอนไปให้ผู้อื่น'.format(name1))
            print('-ScriptSig ของอินพุตของธุรกรรม {} ไม่เข้าคู่กับ ScriptPubkey ของธุรกรรมที่อ้างอิงถึง '.format(name2))
            print('ธุรกรรม {} มีความไม่ถูกต้อง ----> ไม่เพิ่มธุรกรรม {} เข้าไปในบล็อก\n'.format(name2,name2))
        self.tx3 = tx[name3]
        if self.tx3.txverify == True:
            print('ธุรกรรม {} :'.format(name3))
            print('-ธุรกรรม {} มีปริมาณเงินรวมของ Input หรือธุรกรรมก่อนหน้าที่อ้างอิงถึงมากกว่าหรือเท่ากับปริมาณเงินรวมของ Output หรือปริมาณเงินรวมที่จะโอนไปให้ผู้อื่น'.format(name1))
            print('-ScriptSig ของอินพุตของธุรกรรม {} เข้าคู่กับ ScriptPubkey ของธุรกรรมที่อ้างอิงถึง'.format(name3))
            self.verified_transaction.append(self.tx3)
            print('ธุรกรรม {} มีความถูกต้อง ----> เพิ่มธุรกรรม {} เข้าไปในบล็อก\n'.format(name3,name3))
        else:
            print('ธุรกรรม {} :'.format(name3))
            print('-ธุรกรรม {} มีปริมาณเงินรวมของ Input หรือธุรกรรมก่อนหน้าที่อ้างอิงถึงน้อยกว่าหรือเท่ากับปริมาณเงินรวมของ Output หรือปริมาณเงินรวมที่จะโอนไปให้ผู้อื่น'.format(name1))
            print('-ScriptSig ของอินพุตของธุรกรรม {} ไม่เข้าคู่กับ ScriptPubkey ของธุรกรรมที่อ้างอิงถึง '.format(name3))
            print('ธุรกรรม {} มีความไม่ถูกต้อง ----> ไม่เพิ่มธุรกรรม {} เข้าไปในบล็อก\n'.format(name3,name3))
        
        tx_hash1 = bytes.fromhex(self.tx1.id())
        tx_hash1_r  =  tx_hash1[::-1]
        tx_hash2 = bytes.fromhex(self.tx2.id())
        tx_hash2_r  =  tx_hash2[::-1]
        tx_hash3 = bytes.fromhex(self.tx3.id())
        tx_hash3_r  =  tx_hash3[::-1]

        tx_hash = []
        tx_hash.append(tx_hash1_r)
        tx_hash.append(tx_hash2_r)
        tx_hash.append(tx_hash3_r)
            
        self.merkle_root = merkle_root(tx_hash)[::-1] #32 bytes
            
        self.timestamp = int(datetime.datetime.utcnow().timestamp()) #4 bytes
        self.bits = bytes.fromhex('1d00ffff')  #4 bytes
        self.nonce =  ''  #4 bytes
            
        self.block_hashes =  ''

        
        
    def __repr__(self):
           return '[\n   version: {}\n   prev_block: {}\n   merkle_root: {}\n   timestamp: {}\
\n   bits: {}\n   nonce: {}\n   verified_transaction: \n{}\n   block_hashes: {}\n]'.format(
                self.version,
                self.prev_block.hex(),
                self.merkle_root.hex(),
                ctime(time.time()),
                self.bits.hex(),
                #self.nonce.hex(),
                self.nonce,
                self.verified_transaction,
                #self.block_hashes.hex()
                self.block_hashes
            )

    def serialize(self):
        result = int_to_little_endian(self.version, 4)
        result += self.prev_block[::-1]
        result += self.merkle_root[::-1]
        result += int_to_little_endian(self.timestamp, 4)
        result += self.bits
        result += self.nonce
        return result

    def hash(self):
        s = self.serialize()
        h256 = hash256(s)
        return h256[::-1]

    def target(self):
        return bits_to_target(self.bits)

    def difficulty(self):
        lowest = 0xffff * 256**(0x1d - 3)
        return lowest / self.target()

    def check_pow(self):
        h256 = hash256(self.serialize())
        proof = little_endian_to_int(h256)
        return proof < self.target()

#####################################################################################

#################################Merkle_root##########################################
def merkle_parent(hash1, hash2):
     '''Takes the binary hashes and calculates the hash256'''
     return hash256(hash1 + hash2)
    
def merkle_parent_level(hashes):
     '''Takes a list of binary hashes and returns a list that's half
     the length'''
     if len(hashes) == 1:
         raise RuntimeError('Cannot take a parent level with only 1 item')
     if len(hashes) % 2 == 1:
         hashes.append(hashes[-1])
     parent_level = []
     for i in range(0, len(hashes), 2):
         parent = merkle_parent(hashes[i], hashes[i + 1])
         parent_level.append(parent)
     return parent_level

def merkle_root(hashes):
    '''Takes a list of binary hashes and returns the merkle root '''
    # current level starts as hashes
    current_level = hashes
    # loop until there's exactly 1 element
    while len(current_level) > 1:
        # current level becomes the merkle parent level
        current_level = merkle_parent_level(current_level)
    # return the 1st item of the current level
    return current_level[0]
############################################################################################

#################################Proof of work################################################
from hashlib import sha256
import time

MAX_NONCE =  2 ** 32

def mine(block, prefix_zeros):
    header = int_to_little_endian(block.version, 4)
    header += block.prev_block[::-1]
    header += block.merkle_root[::-1]
    header += int_to_little_endian(block.timestamp, 4)
    header += block.bits
    print('------------------------------------------------------------------')
    print('                     กระบวนการ Proof of work')
    print('------------------------------------------------------------------')

    difficulty = 2 ** prefix_zeros
    target = 2 ** (256-prefix_zeros)
   
    
    print("< เริ่มต้นกระบวนการ Proof of work... >")
    print('-จำนวน Leading zero ที่ต้องการ: {}'.format(prefix_zeros))
    print("-ความยาก หรือ Difficulty : {} " .format(difficulty))
    print('-ค่าเป้าหมาย หรือ Target : {}'.format(target))
    print('                                    .')
    print('                                    .')
    print('                                    .')
    start = time.time()
    
    for nonce in range(1,MAX_NONCE+1):
            text = str(header.hex()) +  str(nonce)
            block_hash = hashlib.sha256((str(header)+str(nonce)).encode('utf-8')).hexdigest()
            if int(block_hash, 16) < target:
                break
    total_time = time.time() - start
    print('< สิ้นสุดกระบวนการ Proof of work >')
    print('-ค่า nonce ที่ทำให้กระบวนการ Proof of work สำเร็จ : {}'.format(nonce))
    print('-ค่า Hash ของ block header ที่ทำให้กระบวนการ Proof of work สำเร็จ : {}'.format(block_hash))
    print('-เวลาที่ใช้ในกระบวนการ Proof of work : {} seconds'.format(total_time))
    
    if total_time > 0:
    # estimate the hashes per second
        hash_power = float(nonce/total_time)
        print("-Hashing Power:  {} hashes per second ".format(hash_power))
        print()
    if total_time == 0:
        total_time = 0.01
        hash_power = float(nonce/total_time)
        print("-Hashing Power:  {} hashes per second ".format(hash_power))
        print()
                    
    block.nonce = nonce
    block.block_hashes = block_hash

    if block.type == 'Genesis':
        print('------------------------------------------------------------------')
        print('                 สร้าง Genesis block  สำเร็จ!!!')
        print('------------------------------------------------------------------')
    if block.type == 'Block':
        print('------------------------------------------------------------------')
        print('                        สร้าง Block  สำเร็จ!!!')
        print('------------------------------------------------------------------')
    print('version : {}'.format(block.version))
    print('previous block : {}'.format(block.prev_block.hex()))
    print('merkle root : {}'.format(block.merkle_root.hex()))
    print('timestamp : {}'.format(ctime(time.time())))
    print('bits : {}'.format(block.bits.hex()))
    print('nonce : {}'.format(block.nonce))
    print('verified transaction : ')
    print('------------------------------------------------------------------')
    print('                         Transaction #1')
    print('------------------------------------------------------------------')
    print('{}'.format(block.tx1))
    print('------------------------------------------------------------------')
    print('                         Transaction #2')
    print('------------------------------------------------------------------')
    print('{}'.format(block.tx2))
    print('------------------------------------------------------------------')
    print('                         Transaction #3')
    print('------------------------------------------------------------------')
    print('{}'.format(block.tx3))
    print('block hash : {}'.format(block.block_hashes))

    print()
    check_pow(target,block)
   
    
    return None

def check_pow(target,block):

    header = int_to_little_endian(block.version, 4)
    header += block.prev_block[::-1]
    header += block.merkle_root[::-1]
    header += int_to_little_endian(block.timestamp, 4)
    header += block.bits
    block_hash = hashlib.sha256((str(header)+str(block.nonce)).encode('utf-8')).hexdigest()
    
    print('------------------------------------------------------------------------------------------------')
    print('         แพร่กระจาย Block ไปยัง Miner คนอื่น ๆ ในเครือข่ายบล็อกเชน')
    print('------------------------------------------------------------------------------------------------')
    print('< กระบวนการตรวจสอบความถูกต้องของ Block.... >')
    if int(block_hash, 16) < target:
            blockchain.append(block)
            print('-Block มีความถูกต้อง -----> เพิ่ม Block เข้าไปใน blockchain\n')
            last_block_hash.append(block_hash)
            if block.type == 'Genesis':
             #Tx1
                receiver1 = find_user[block.name1][1]
                amount = (find_amount[block.name1][0])/(1000000)
                print('>>> เงินโอนไปยัง {} ด้วยจำนวนเงิน {} '.format(receiver1.name,amount))
                receiver1.deposit(amount)
            #Tx2
                receiver2 = find_user[block.name2][1]
                amount = (find_amount[block.name2][0])/(1000000)
                print('>>> เงินโอนไปยัง {} ด้วยจำนวนเงิน {} '.format(receiver2.name,amount))
                receiver2.deposit(amount)
            #Tx3
                receiver3 = find_user[block.name3][1]
                amount = (find_amount[block.name3][0])/(1000000)
                print('>>> เงินโอนไปยัง {} ด้วยจำนวนเงิน {} '.format(receiver3.name,amount))
                receiver3.deposit(amount)
            if block.type == 'Block':
            #Tx1
                sender1 = find_user[block.name1][0]
                receiver1 = find_user[block.name1][1]
                amount = (find_amount[block.name1][1])/(1000000)
                print('>>> เงินโอนจาก {} ไปยัง {} ด้วยจำนวนเงิน {} '.format(sender1.name,receiver1.name,amount))
                sender1.withdraw(amount)
                receiver1.deposit(amount)
            #Tx2
                sender2 = find_user[block.name2][0]
                receiver2 = find_user[block.name2][1]
                amount = (find_amount[block.name2][1])/(1000000)
                print('>>> เงินโอนจาก {} ไปยัง {} ด้วยจำนวนเงิน {} '.format(sender2.name,receiver2.name,amount))
                sender2.withdraw(amount)
                receiver2.deposit(amount)
            #Tx3
                sender3 = find_user[block.name3][0]
                receiver3 = find_user[block.name3][1]
                amount = (find_amount[block.name3][1])/(1000000)
                print('>>> เงินโอนจาก {} ไปยัง {} ด้วยจำนวนเงิน {} '.format(sender3.name,receiver3.name,amount))
                sender3.withdraw(amount)
                receiver3.deposit(amount)
               
    else:
            print('-Block ไม่มีความถูกต้อง')
    return None
##########################################################################################################################################################################


