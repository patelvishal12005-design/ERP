import requests

login_data = {'username': 'testadmin', 'password': 'admin123'}
token = requests.post('http://127.0.0.1:8000/api/token/', json=login_data).json().get('access')

res = requests.post('http://127.0.0.1:8000/api/employees/', json={'name': 'newuser2', 'email': 'newuser2@gmail.com', 'role': 'sell', 'department': 'Engineering', 'salary': '100000'}, headers={'Authorization': f'Bearer {token}'})

with open('error500.html', 'wb') as f:
    f.write(res.content)
print(res.status_code)
