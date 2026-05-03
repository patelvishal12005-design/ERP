import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Erpbecend.settings')
django.setup()

from django.contrib.auth.models import User
from ERP.serializers import EmployeeSerializer
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

user = User.objects.get(username='testadmin')
factory = APIRequestFactory()
django_request = factory.post('/api/employees/', {
    'name': 'vishal',
    'email': 'vishal13@gmail.com',
    'role': 'sels',
    'department': 'Sales',
    'salary': '10000'
})
django_request.user = user
request = Request(django_request)

serializer = EmployeeSerializer(data=request.data, context={'request': request})
if serializer.is_valid():
    try:
        serializer.save(user=user)
        print("Success!")
    except Exception as e:
        import traceback
        traceback.print_exc()
else:
    print("Validation failed:", serializer.errors)
