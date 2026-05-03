from rest_framework import serializers
from django.utils import timezone
from .models import Employee, InventoryItem, FinanceRecord, SaleRecord, Attendance
from django.contrib.auth.models import User

class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'password', 'email']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password']
        )
        return user


class EmployeeSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    today_status = serializers.SerializerMethodField()
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Employee
        fields = '__all__'
        validators = []

    def validate_email(self, value):
        request = self.context.get('request')
        if request and request.user:
            # Check if an employee with this email already exists for the current user
            qs = Employee.objects.filter(user=request.user, email=value)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError("employee with this email already exists.")
        return value

    def get_today_status(self, obj):
        today = timezone.now().date()
        att = obj.attendance_records.filter(date=today).first()
        return att.status if att else None


class InventoryItemSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = InventoryItem
        fields = '__all__'


class FinanceRecordSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    class Meta:
        model = FinanceRecord
        fields = '__all__'


class SaleRecordSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    total = serializers.ReadOnlyField()

    class Meta:
        model = SaleRecord
        fields = '__all__'
