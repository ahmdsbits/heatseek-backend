from time import strptime

from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import action
from rest_framework.exceptions import (
    NotFound,
    PermissionDenied,
    ValidationError,
)
from rest_framework.response import Response

from .filters import AttendanceFilter, EmployeeFilter, LeaveRequestFilter
from .models import Attendance, Employee, LeaveRequest
from .permissions import IsPrivileged
from .serializers import (
    AttendanceSerializer,
    EmployeeAuthTokenSerializer,
    EmployeeSerializer,
    LeaveRequestSerializer,
)


class LoginView(ObtainAuthToken):
    serializer_class = EmployeeAuthTokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "employee_id": user.employee_id})


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all().order_by("employee_id")
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "employee_id"

    filter_backends = [DjangoFilterBackend]
    filterset_class = EmployeeFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        employee_id = self.kwargs.get("employee_id")

        if self.request.user.employee_type == "PRIVILEGED" and employee_id:  # pyright: ignore
            return queryset.filter(employee_id=employee_id)

        if (
            self.request.user.employee_type == "GENERAL"  # pyright: ignore
            and employee_id
            and employee_id != self.request.user.employee_id  # pyright: ignore
        ):
            raise PermissionDenied("You are not authorized to access this resource")

        if self.request.user.employee_type == "GENERAL":  # pyright: ignore
            return queryset.filter(id=self.request.user.id)  # pyright: ignore

        return queryset

    def create(self, request, *args, **kwargs):
        if request.user.employee_type != "PRIVILEGED":  # pyright: ignore
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        data = request.data

        if not data.get("first_name"):
            raise ValidationError("First name must be provided")
        if not data.get("last_name"):
            raise ValidationError("Last name must be provided")
        if not data.get("email"):
            raise ValidationError("Email must be provided")
        if not data.get("employee_id"):
            raise ValidationError("Employee ID must be provided")
        if not data.get("employee_type"):
            raise ValidationError("Employee ID must be provided")
        if not data.get("password"):
            raise ValidationError("Password must be provided")

        return super().create(request, args, kwargs)

    def partial_update(self, request, *args, **kwargs):
        if not self.kwargs.get("employee_id"):
            return Response(
                "Employee ID is required",
                status=status.HTTP_400_BAD_REQUEST,
            )
        if request.user.employee_id != self.kwargs.get("employee_id"):  # pyright: ignore
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        return super().partial_update(request, args, kwargs)

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_superuser:  # pyright: ignore
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        return super().destroy(request, args, kwargs)


class MonthlyAttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        employee_id = self.kwargs.get("employee_id")

        if self.request.user.employee_type == "GENERAL":  # pyright: ignore
            if employee_id and employee_id != self.request.user.employee_id:  # pyright: ignore
                raise PermissionDenied("You are unauthorized to access this resource")
            queryset = queryset.filter(employee=self.request.user)

        if not employee_id:
            employee_id = self.request.user.employee_id

        queryset = queryset.filter(employee__employee_id=employee_id)
        return queryset

    def list(self, request, *args, **kwargs):
        employee_id = self.kwargs.get("employee_id")

        if self.request.user.employee_type == "GENERAL":  # pyright: ignore
            if employee_id and employee_id != self.request.user.employee_id:  # pyright: ignore
                raise PermissionDenied("You are unauthorized to access this resource")

        if not employee_id:
            employee_id = self.request.user.employee_id

        employee = Employee.objects.get(employee_id=employee_id)

        month = self.kwargs.get("month")
        if not month:
            return Response(
                "A month must be provided", status=status.HTTP_400_BAD_REQUEST
            )

        from datetime import datetime, timedelta

        from django.utils import timezone

        today = timezone.now().date()
        try:
            start_date = datetime.strptime(month + "-01", "%Y-%m-%d").date()
        except Exception:
            return Response(
                "Month must be in YYYY-MM format", status=status.HTTP_400_BAD_REQUEST
            )

        import calendar

        _, num_days = calendar.monthrange(start_date.year, start_date.month)
        end_date = start_date.replace(day=num_days)

        prev_end_date = start_date.replace(day=1) - timedelta(days=1)
        prev_start_date = prev_end_date.replace(day=1)

        # 2. Get actual DB entries
        logs = self.get_queryset().filter(
            date__range=[start_date, end_date],
        )
        prev_logs = self.get_queryset().filter(
            date__range=[prev_start_date, prev_end_date]
        )
        # Convert to a dictionary for fast lookup: { date_obj: log_obj }
        logs_dict = {log.date: log for log in logs}
        prev_logs_dict = {log.date: log for log in prev_logs}

        # 3. Generate the full list (The "Gap Filling")
        full_report = {
            "employee_id": employee_id,
            "absent_this_month": 0,
            "absent_last_month": 0,
            "available_paid_leaves": employee.available_paid_leaves,
            "logs": [],
        }

        current_check = start_date
        while current_check <= end_date:
            if current_check < employee.date_joined.date() or current_check > today:
                current_check += timedelta(days=1)
                continue
            if current_check in logs_dict:
                entry = logs_dict[current_check]
                full_report["logs"].append(
                    {
                        "date": current_check,
                        "day": calendar.day_name[current_check.weekday()],
                        "status": entry.status,  # e.g., 'Present', 'Late'
                    }
                )
            else:
                full_report["absent_this_month"] += 1
                full_report["logs"].append(
                    {
                        "date": current_check,
                        "day": calendar.day_name[current_check.weekday()],
                        "status": "ABSENT",
                    }
                )

            current_check += timedelta(days=1)

        current_check = prev_start_date
        while current_check <= prev_end_date:
            if current_check < employee.date_joined.date() or current_check > today:
                current_check += timedelta(days=1)
                continue
            if current_check not in prev_logs_dict:
                full_report["absent_last_month"] += 1

            current_check += timedelta(days=1)

        return Response(full_report)


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all().order_by("date")
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = AttendanceFilter

    def get_object(self):
        date = self.kwargs.get("date")
        employee_id = self.kwargs.get("employee_id")

        obj = get_object_or_404(
            self.get_queryset(), date=date, employee__employee_id=employee_id
        )

        # 3. Check permissions (standard DRF practice)
        self.check_object_permissions(self.request, obj)

        return obj

    def get_queryset(self):
        queryset = super().get_queryset()
        date_str = self.kwargs.get("date")
        employee_id = self.kwargs.get("employee_id")

        if self.request.user.employee_type == "GENERAL":  # pyright: ignore
            if employee_id and employee_id != self.request.user.employee_id:  # pyright: ignore
                raise PermissionDenied("You are unauthorized to access this resource")
            queryset = queryset.filter(employee=self.request.user)

        if employee_id:
            queryset = queryset.filter(employee__employee_id=employee_id)

        if date_str:
            try:
                from datetime import datetime

                date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                raise ValidationError("Date format in URL must be YYYY-MM-DD")
            queryset = queryset.filter(date=date_obj)

        return queryset

    def create(self, request, *args, **kwargs):
        if request.user.employee_type != "PRIVILEGED":  # pyright: ignore
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        data = request.data

        try:
            employee = Employee.objects.get(employee_id=data["employee_id"])
        except Employee.DoesNotExist:
            raise NotFound(f"Employee with ID '{data['employee_id']}' not found")

        if employee == request.user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        try:
            if Attendance.objects.get(date=data.get("date"), employee=employee):
                return Response(
                    "Duplicate attendance entries cannot exist",
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Attendance.DoesNotExist:
            pass

        return super().create(request, args, kwargs)

    def partial_update(self, request, *args, **kwargs):
        if request.user.employee_type != "PRIVILEGED":  # pyright: ignore
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        return super().partial_update(request, args, kwargs)

    def destroy(self, request, *args, **kwargs):
        if not request.user.is_superuser:  # pyright: ignore
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        return super().destroy(request, args, kwargs)


class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = LeaveRequest.objects.all().order_by("date")
    serializer_class = LeaveRequestSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "uuid"
    filterset_class = LeaveRequestFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        uuid = self.kwargs.get("uuid")

        if self.request.user.employee_type == "GENERAL":  # pyright: ignore
            if (
                uuid
                and LeaveRequest.objects.get(uuid=uuid).employee.employee_id
                != self.request.user.employee_id  # pyright: ignore
            ):
                raise PermissionDenied("You are not authorized to access this resource")

        if uuid:  # pyright: ignore
            queryset = queryset.filter(uuid=uuid)

        return queryset

    def create(self, request, *args, **kwargs):
        if request.user.available_paid_leaves > 0:  # pyright: ignore
            data = request.data.copy()
            data["status"] = LeaveRequest.ApprovalStatus.PENDING

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                "No available paid leaves", status=status.HTTP_400_BAD_REQUEST
            )

    def perform_create(self, serializer):
        serializer.save(employee=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()

        if request.user.employee_type == "GENERAL":  # pyright: ignore
            if instance.status != LeaveRequest.ApprovalStatus.PENDING:
                return Response(
                    "Leave requests can only be updated when in PENDING state",
                    status=status.HTTP_400_BAD_REQUEST,
                )

        return super().update(request, args, kwargs)

    @action(detail=True, methods=["post"], permission_classes=[IsPrivileged])
    def approve(self, request, *args, **kwargs):
        leave_request = self.get_object()
        if leave_request.employee == request.user:
            return Response(
                "You cannot approve your own leave request",
                status=status.HTTP_400_BAD_REQUEST,
            )
        if leave_request.status == LeaveRequest.ApprovalStatus.PENDING:
            leave_request.status = LeaveRequest.ApprovalStatus.APPROVED
            leave_request.processor = request.user
            leave_request.response_message = request.data.get("response_message")
            leave_request.employee.available_paid_leaves -= 1
            leave_request.employee.save()
            leave_request.save()
            Attendance.objects.create(
                employee=leave_request.employee,
                date=leave_request.date,
                status="ON_LEAVE",
            )
            return Response("Leave request approved")
        else:
            return Response(
                "Leave request is not in PENDING state",
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"], permission_classes=[IsPrivileged])
    def deny(self, request, *args, **kwargs):
        leave_request = self.get_object()
        if leave_request.employee == request.user:
            return Response(
                "You cannot deny your own leave request",
                status=status.HTTP_400_BAD_REQUEST,
            )
        if leave_request.status == LeaveRequest.ApprovalStatus.PENDING:
            leave_request.status = LeaveRequest.ApprovalStatus.DENIED
            leave_request.processor = request.user
            leave_request.response_message = request.data.get("response_message")
            leave_request.save()
            return Response("Leave request denied")
        else:
            return Response(
                "Leave request is not in PENDING state",
                status=status.HTTP_400_BAD_REQUEST,
            )
