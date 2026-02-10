"""
Profile forms.
"""
from django import forms

from ..models import User, Profile


class ProfileForm(forms.ModelForm):
    """Profile update form."""

    # User fields
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = Profile
        fields = [
            "phone",
            "bio",
            "avatar",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
        ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)

        # Update user fields
        if self.user:
            self.user.first_name = self.cleaned_data.get("first_name", "")
            self.user.last_name = self.cleaned_data.get("last_name", "")
            if commit:
                self.user.save(update_fields=["first_name", "last_name"])

        if commit:
            # Create profile if it doesn't exist
            if not profile.pk and self.user:
                profile.user = self.user
            profile.save()

        return profile


class UserSettingsForm(forms.ModelForm):
    """User settings form (timezone, language, etc.)."""

    class Meta:
        model = User
        fields = ["timezone", "language"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["timezone"].widget = forms.Select(choices=[
            ("America/Sao_Paulo", "São Paulo (GMT-3)"),
            ("America/New_York", "New York (GMT-5)"),
            ("Europe/London", "London (GMT+0)"),
            ("UTC", "UTC"),
        ])
        self.fields["language"].widget = forms.Select(choices=[
            ("pt-br", "Português (Brasil)"),
            ("en", "English"),
            ("es", "Español"),
        ])
