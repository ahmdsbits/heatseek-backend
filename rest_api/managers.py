from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    def create_user(
        self,
        employee_id,
        employee_type,
        first_name,
        last_name,
        email,
        password,
        **extra_fields,
    ):
        if not email:
            raise ValueError(_("Email must be set"))
        if not employee_id:
            raise ValueError(_("Employee ID must be set"))
        if not first_name:
            raise ValueError(_("First Name must be set"))
        if not last_name:
            raise ValueError(_("Last Name must be set"))
        email = self.normalize_email(email)
        user = self.model(
            employee_id=employee_id,
            employee_type=employee_type,
            first_name=first_name,
            last_name=last_name,
            email=email,
            **extra_fields,
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(
        self,
        employee_id,
        employee_type,
        first_name,
        last_name,
        email,
        password,
        **extra_fields,
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(
            employee_id,
            employee_type,
            first_name,
            last_name,
            email,
            password,
            **extra_fields,
        )
