import django_filters
from django.db.models import Value
from django.db.models.functions import Concat

from .models import Attendance, Employee, LeaveRequest


class EmployeeFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(method="filter_by_full_name")

    class Meta:
        model = Employee
        fields = ["employee_id", "email", "employee_type", "first_name", "last_name"]

    def filter_by_full_name(self, queryset, name, value):
        return queryset.annotate(
            full_name=Concat("first_name", Value(" "), "last_name")
        ).filter(full_name__icontains=value)


class AttendanceFilter(django_filters.FilterSet):
    employee_id = django_filters.CharFilter(field_name="employee__employee_id")
    date = django_filters.DateFilter()
    status = django_filters.ChoiceFilter()

    class Meta:
        model = Attendance
        fields = []


class LeaveRequestFilter(django_filters.FilterSet):
    uuid = django_filters.NumberFilter()
    created_at = django_filters.DateTimeFilter()
    employee_id = django_filters.CharFilter(field_name="employee__employee_id")
    date = django_filters.DateFilter()
    message = django_filters.CharFilter(lookup_expr="icontains")
    status = django_filters.CharFilter()
    processor = django_filters.CharFilter(field_name="processor__employee_id")
    response_message = django_filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = LeaveRequest
        fields = []
