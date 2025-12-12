import random

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

from .managers import CustomUserManager


class Employee(AbstractUser):
    objects = CustomUserManager()

    class Type(models.TextChoices):
        GENERAL = "GENERAL", "General Employee"
        PRIVILEGED = "PRIVILEGED", "Privileged Employee"

    username = None
    employee_type = models.CharField(
        max_length=20, choices=Type.choices, default=Type.GENERAL
    )
    employee_id = models.CharField(max_length=20, unique=True)
    available_paid_leaves = models.PositiveIntegerField(default=15)

    USERNAME_FIELD = "employee_id"
    REQUIRED_FIELDS = [
        "employee_type",
        "first_name",
        "last_name",
        "email",
    ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Attendance(models.Model):
    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        LATE = "LATE", "Late"
        ABSENT = "ABSENT", "Absent"
        ON_LEAVE = "ON_LEAVE", "On Leave"

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="attendances"
    )
    date = models.DateField(default=timezone.now)
    status = models.TextField(max_length=20, choices=Status.choices)

    class Meta:
        unique_together = "employee", "date"

    def __str__(self):
        return f"{self.employee.first_name} {self.employee.last_name} - {self.date} - {self.status}"


def gen_num_uuid():
    return random.randint(1000000000, 9999999999)


class LeaveRequest(models.Model):
    class ApprovalStatus(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        DENIED = "DENIED", "Denied"

    uuid = models.BigIntegerField(
        primary_key=True, default=gen_num_uuid, editable=False
    )
    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="leave_requests"
    )
    processor = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="processed_leaves",
    )
    status = models.TextField(
        max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING
    )
    date = models.DateField()
    message = models.CharField(blank=True, null=True)
    response_message = models.CharField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Request #{self.uuid} - {self.employee.first_name} {self.employee.last_name} - {self.date} - {self.status}"
