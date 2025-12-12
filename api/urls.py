from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework import routers

from rest_api.views import (
    AttendanceViewSet,
    EmployeeViewSet,
    LeaveRequestViewSet,
    LoginView,
    MonthlyAttendanceViewSet,
)

router = routers.DefaultRouter()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("api/login/", LoginView.as_view(), name="login"),
    path(
        "api/employees/",
        EmployeeViewSet.as_view(
            {"get": "list", "post": "create", "patch": "partial_update"}
        ),
        name="employee-list",
    ),
    path(
        "api/employees/<str:employee_id>/",
        EmployeeViewSet.as_view({"get": "retrieve"}),
        name="employee-detail",
    ),
    path(
        "api/attendances/",
        AttendanceViewSet.as_view({"get": "list", "post": "create"}),
        name="attendance-list",
    ),
    re_path(
        r"^api/attendances/(?P<date>\d{4}-\d{2}-\d{2})/$",
        AttendanceViewSet.as_view(
            {
                "get": "list",
            }
        ),
        name="attendance-list-by-date",
    ),
    re_path(
        r"^api/attendances/(?P<date>\d{4}-\d{2}-\d{2})/(?P<employee_id>.+)/$",
        AttendanceViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="attendance-detail",
    ),
    re_path(
        r"^api/attendances/(?P<month>\d{4}-\d{2})/$",
        MonthlyAttendanceViewSet.as_view({"get": "list"}),
    ),
    re_path(
        r"^api/attendances/(?P<month>\d{4}-\d{2})/(?P<employee_id>.+)/$",
        MonthlyAttendanceViewSet.as_view({"get": "list"}),
    ),
    path(
        "api/leave-requests/",
        LeaveRequestViewSet.as_view(
            {
                "get": "list",
                "post": "create",
            }
        ),
        name="leave-request-list",
    ),
    path(
        "api/leave-requests/<int:uuid>/",
        LeaveRequestViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="leave-request-detail",
    ),
    path(
        "api/leave-requests/<int:uuid>/approve/",
        LeaveRequestViewSet.as_view(
            {
                "post": "approve",
            }
        ),
        name="leave-request-approve",
    ),
    path(
        "api/leave-requests/<int:uuid>/deny/",
        LeaveRequestViewSet.as_view(
            {
                "post": "deny",
            }
        ),
        name="leave-request-deny",
    ),
]
