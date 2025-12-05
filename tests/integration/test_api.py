# Add your API integration testing code here# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import json
import requests
import logging

# Enable logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

new_user_id = ""
new_user = {"name": "John Doe"}

def test_access_to_the_users_without_authentication(global_config):
    response = requests.get(global_config["APIEndpoint"] + '/users')
    assert response.status_code == 401

def test_get_list_of_users_by_regular_user(global_config):
    response = requests.get(
        global_config["APIEndpoint"] + '/users',
        headers={'Authorization': global_config["regularUserIdToken"]}
    )
    assert response.status_code == 403

def test_deny_post_user_by_regular_user(global_config):
    response = requests.post(
        global_config["APIEndpoint"] + '/users',
        data=json.dumps(new_user),
        headers={'Authorization': global_config["regularUserIdToken"],
                 'Content-Type': 'application/json'}
    )
    assert response.status_code == 403

def test_allow_post_user_by_administrative_user(global_config):
    response = requests.post(
        global_config["APIEndpoint"] + '/users',
        data=json.dumps(new_user),
        headers={'Authorization': global_config["adminUserAccessToken"],
                 'Content-Type': 'application/json'}
    )
    assert response.status_code == 201
    data = json.loads(response.text)
    assert data['name'] == new_user['name']
    global new_user_id
    new_user_id = data['userid']

def test_deny_post_invalid_user(global_config):
    new_invalid_user = {"Name": "John Doe"}
    response = requests.post(
        global_config["APIEndpoint"] + '/users',
        data=new_invalid_user,
        headers={'Authorization': global_config["adminUserAccessToken"],
                 'Content-Type': 'application/json'}
    )
    assert response.status_code == 400

def test_get_user_by_regular_user(global_config):
    response = requests.get(
        global_config["APIEndpoint"] + f'/users/{new_user_id}',
        headers={'Authorization': global_config["regularUserIdToken"]}
    )
    assert response.status_code == 403

# ========== NEW TESTS ==========

def test_regular_user_can_access_own_data(global_config):
    """Verify that regular users have access to their own data"""
    # Trước tiên tạo profile cho regular user
    create_response = requests.put(
        global_config["APIEndpoint"] + f'/users/{global_config["regularUserSub"]}',
        data=json.dumps({"name": "Regular User", "email": "regular@example.com"}),
        headers={
            'Authorization': global_config["regularUserIdToken"],
            'Content-Type': 'application/json'
        }
    )
    assert create_response.status_code == 200
    
    # Bây giờ GET để verify có thể truy cập
    response = requests.get(
        global_config["APIEndpoint"] + f'/users/{global_config["regularUserSub"]}',
        headers={'Authorization': global_config["regularUserIdToken"]}
    )
    assert response.status_code == 200
    data = json.loads(response.text)
    assert data['userid'] == global_config["regularUserSub"]
    assert data['name'] == "Regular User"

def test_regular_user_can_update_own_data(global_config):
    """Verify that regular users can change their own data"""
    updated_data = {"name": "Regular User Updated", "email": "regular@example.com"}
    response = requests.put(
        global_config["APIEndpoint"] + f'/users/{global_config["regularUserSub"]}',
        data=json.dumps(updated_data),
        headers={
            'Authorization': global_config["regularUserIdToken"],
            'Content-Type': 'application/json'
        }
    )
    assert response.status_code == 200
    data = json.loads(response.text)
    assert data['name'] == updated_data['name']
    assert data['userid'] == global_config["regularUserSub"]

def test_regular_user_can_delete_own_data(global_config):
    """Verify that regular users can delete their own data"""
    response = requests.delete(
        global_config["APIEndpoint"] + f'/users/{global_config["regularUserSub"]}',
        headers={'Authorization': global_config["regularUserIdToken"]}
    )
    assert response.status_code == 200
    # Verify deletion
    data = json.loads(response.text)
    assert 'message' in data or data == {}

def test_admin_can_list_all_users(global_config):
    """Verify that an administrative user can list all users"""
    response = requests.get(
        global_config["APIEndpoint"] + '/users',
        headers={'Authorization': global_config["adminUserAccessToken"]}
    )
    assert response.status_code == 200
    data = json.loads(response.text)
    # Code đã sửa trả về {'items': [...]}
    assert 'items' in data
    assert isinstance(data['items'], list)

def test_admin_can_delete_existing_user(global_config):
    """Verify that an administrative user can delete an existing user"""
    # Sử dụng new_user_id từ test trước (user được tạo bởi admin)
    response = requests.delete(
        global_config["APIEndpoint"] + f'/users/{new_user_id}',
        headers={'Authorization': global_config["adminUserAccessToken"]}
    )
    assert response.status_code == 200
    data = json.loads(response.text)
    assert 'message' in data or data == {}