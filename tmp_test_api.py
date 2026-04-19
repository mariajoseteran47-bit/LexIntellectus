import httpx
import logging

logging.basicConfig(level=logging.INFO)

auth_data = {
    'username': 'admin@lexintellectus.com',
    'password': 'admin123',
    'client_id': 'string',
    'client_secret': 'string'
}

with httpx.Client() as client:
    r = client.post('http://localhost:8000/api/v1/auth/login', data=auth_data)
    if r.status_code == 200:
        token = r.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}
        cases_r = client.get('http://localhost:8000/api/v1/cases', headers=headers)
        print("Status code:", cases_r.status_code)
        print("Response JSON:", cases_r.json())
    else:
        print("Login failed", r.status_code, r.text)
