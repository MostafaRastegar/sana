import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class StrongPasswordValidator:
    def validate(self, password, user=None):
        if not re.search(r"[A-z]", password):
            raise ValidationError(_("Password must contain at least one letter."))

        if not re.search(r"[a-z]", password):
            raise ValidationError(
                _("Password must contain at least one lowercase letter.")
            )

        if not re.search(r"[0-9]", password):
            raise ValidationError(_("Password must contain at least one number."))

        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValidationError(
                _("Password must contain at least one special character.")
            )

    def get_help_text(self):
        return _("Password must contain number.")
