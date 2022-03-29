import boto3

dynamodb = boto3.resource('dynamodb',
  aws_access_key_id='AKIATXFWJZHNC2HIQPPF',
  aws_secret_access_key='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',
  region_name='us-east-2')



table = dynamodb.Table('Music')

response = table.scan()
data = response['Items']
print(data)
while 'LastEvaluatedKey' in response:
    response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
    data.extend(response['Items'])

print(data)
print(list(dynamodb.tables.all()))
for table in dynamodb.tables.all():
    print(table.attribute_definitions)