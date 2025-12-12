from rest_framework import serializers
from rest_framework.authtoken.serializers import AuthTokenSerializer

from .models import Attendance, Employee, LeaveRequest


class EmployeeAuthTokenSerializer(AuthTokenSerializer):
    username = None  # pyright: ignore
    employee_id = serializers.CharField(label="Employee ID", write_only=True)

    def validate(self, attrs):
        attrs["username"] = attrs.get("employee_id")
        return super().validate(attrs)


class EmployeeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:  # pyright: ignore
        model = Employee
        fields = [
            "employee_id",
            "employee_type",
            "first_name",
            "last_name",
            "email",
            "password",
            "available_paid_leaves",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        password = validated_data.pop("password")
        employee = Employee(**validated_data)
        employee.set_password(password)
        employee.save()
        return employee

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        instance = super().update(instance, validated_data)

        if password:
            instance.set_password(password)
            instance.save()

        return instance


class AttendanceSerializer(serializers.HyperlinkedModelSerializer):
    employee_id = serializers.SlugRelatedField(
        queryset=Employee.objects.all(),
        slug_field="employee_id",
        source="employee",
    )

    class Meta:  # pyright: ignore
        model = Attendance
        fields = [
            "date",
            "employee_id",
            "status",
        ]

    def get_fields(self):
        fields = super().get_fields()
        if self.instance:  # If instance is passed, it's an update
            fields["employee_id"].read_only = True
            fields["date"].read_only = True
        return fields


class LeaveRequestSerializer(serializers.HyperlinkedModelSerializer):
    employee = EmployeeSerializer(read_only=True)
    processor = EmployeeSerializer(read_only=True)

    class Meta:  # pyright: ignore
        model = LeaveRequest
        fields = [
            "uuid",
            "created_at",
            "employee",
            "date",
            "message",
            "status",
            "processor",
            "response_message",
        ]
        extra_kwargs = {
            "message": {"required": False},
            "response_message": {"required": False},
        }
