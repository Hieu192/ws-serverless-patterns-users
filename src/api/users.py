# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import uuid
import os
import boto3
from datetime import datetime, timezone

# test aaaaassssssss 2

# Prepare DynamoDB client
USERS_TABLE = os.getenv('USERS_TABLE')
if not USERS_TABLE:
    raise ValueError('USERS_TABLE environment variable is required')

dynamodb = boto3.resource('dynamodb')
ddbTable = dynamodb.Table(USERS_TABLE)

def lambda_handler(event, context):
    route_key = f"{event['httpMethod']} {event['resource']}"

    # Set default response, override with data from DynamoDB if any
    response_body = {'Message': 'Unsupported route'}
    status_code = 400
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
        }

    # try:
        if route_key == 'GET /users/count':
            my_invalid_function()
            ddb_response = ddbTable.scan(Select='COUNT')
            # return list of items instead of full DynamoDB response
            response_body = {'CountTestVip': ddb_response['Count']}
            status_code = 200

        # Get a list of all Users with pagination
        if route_key == 'GET /users':
            scan_kwargs = {'Select': 'ALL_ATTRIBUTES', 'Limit': 100}
            
            query_params = event.get('queryStringParameters') or {}
            if query_params.get('nextToken'):
                try:
                    scan_kwargs['ExclusiveStartKey'] = json.loads(query_params['nextToken'])
                except (json.JSONDecodeError, TypeError, KeyError):
                    pass
            
            ddb_response = ddbTable.scan(**scan_kwargs)
            response_body = {'items': ddb_response['Items']}
            
            if 'LastEvaluatedKey' in ddb_response:
                response_body['nextToken'] = json.dumps(ddb_response['LastEvaluatedKey'])
            
            status_code = 200

        # CRUD operations for a single User
       
        # Read a user by ID
        if route_key == 'GET /users/{userid}':
            userid = event.get('pathParameters', {}).get('userid', '')
            ddb_response = ddbTable.get_item(Key={'userid': userid})
            if 'Item' in ddb_response:
                response_body = ddb_response['Item']
            else:
                response_body = {}
            status_code = 200
        
        # Delete a user by ID
        if route_key == 'DELETE /users/{userid}':
            userid = event.get('pathParameters', {}).get('userid', '')
            ddbTable.delete_item(Key={'userid': userid})
            response_body = {'message': 'User deleted successfully'}
            status_code = 200
        
        # Create a new user 
        if route_key == 'POST /users':
            if not event.get('body'):
                response_body = {'Error': 'Request body is required'}
                status_code = 400
            else:
                request_json = json.loads(event['body'])
                request_json['timestamp'] = datetime.now(timezone.utc).isoformat()
                # generate unique id if it isn't present in the request
                if 'userid' not in request_json:
                    request_json['userid'] = str(uuid.uuid4())
                # update the database
                ddbTable.put_item(Item=request_json)
                response_body = request_json
                status_code = 201

        # Update a specific user by ID
        if route_key == 'PUT /users/{userid}':
            userid = event.get('pathParameters', {}).get('userid', '')
            if not event.get('body'):
                response_body = {'Error': 'Request body is required'}
                status_code = 400
            else:
                request_json = json.loads(event['body'])
                request_json['timestamp'] = datetime.now(timezone.utc).isoformat()
                request_json['userid'] = userid
                # update the database
                ddbTable.put_item(Item=request_json)
                response_body = request_json
                status_code = 200
    # except json.JSONDecodeError:
    #     status_code = 400
    #     response_body = {'Error': 'Invalid JSON in request body'}
    # except KeyError as err:
    #     status_code = 400
    #     response_body = {'Error': f'Missing required field: {str(err)}'}
    # except Exception as err:
    #     status_code = 500
    #     response_body = {'Error': 'Internal server error'}
    #     print(f'Error: {str(err)}')
    return {
        'statusCode': status_code,
        'body': json.dumps(response_body),
        'headers': headers
    }