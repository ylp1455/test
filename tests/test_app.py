import json

def test_home_endpoint(client):
    response = client.get('/api/v1/health')
    assert response.status_code == 200
    expected = {
        "data": "I am fine! Not connected to DB",
        "status": 200
    }
    json.loads(response.get_data(as_text=True))

def test_insert_data(client):
    sample_data = {
        "email":"test1@test.com",
        "password":"12345679",
        "phone_number":"0772193833"
    }
    
    response = client.post('/api/v1/user', json=sample_data)
    
    assert response.status_code == 201
    expected = {
        "message": "User inserted successfully"
    }
    json.loads(response.get_data(as_text=True))

def test_login(client):
    sample_data = {
        "email":"test1@test.com",
        "password":"12345679",
    }
    
    response = client.post('/api/v1/login', json=sample_data)
    
    assert response.status_code == 200
    expected = {
        "user_id": "1"
    }
    json.loads(response.get_data(as_text=True))