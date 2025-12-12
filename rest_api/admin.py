from django.contrib import admin

from .models import Attendance, Employee, LeaveRequest


class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "employee_id",
        "employee_type",
        "name",
        "email",
        "available_paid_leaves",
    )

    def name(self, employee):
        return employee.get_full_name() if employee else "N/A"


class AttendanceAdmin(admin.ModelAdmin):
    list_display = ("date", "employee_id", "name", "status")

    def name(self, attendance):
        return attendance.employee.get_full_name() if attendance.employee else "N/A"

    def employee_id(self, attendance):
        return attendance.employee.employee_id if attendance.employee else "N/A"


class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "created_at",
        "employee_id",
        "name",
        "date",
        "message",
        "status",
        "processor",
        "response_message",
    )

    def name(self, attendance):
        return attendance.employee.get_full_name() if attendance.employee else "N/A"

    def employee_id(self, attendance):
        return attendance.employee.employee_id if attendance.employee else "N/A"


admin.site.register(Employee, EmployeeAdmin)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(LeaveRequest, LeaveRequestAdmin)
