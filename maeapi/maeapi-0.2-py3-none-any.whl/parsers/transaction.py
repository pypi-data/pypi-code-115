
import json

def parse_spending_patterns(response):
    return response["spendingPatterns"]

def parse_transaction_history(response):
    res = []
    for i in response["historyItemList"]:
        for j in i['historyList']:
            res.append({
                'btsId':j['btsId'],
                'transactionDate':j['transactionDate'],
                'amount':j['amount'],
                'btsDescription':j['btsDescription']})
            
    return res