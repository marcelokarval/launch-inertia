"""
Contact forms.
"""
from django import forms

from ..models import Contact, Tag


class ContactForm(forms.ModelForm):
    """Form for creating and editing contacts."""

    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.active(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Contact
        fields = [
            "name",
            "email",
            "phone",
            "company",
            "job_title",
            "status",
            "source",
            "notes",
            "tags",
            "custom_fields",
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email", "")
        if email:
            return email.lower().strip()
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get("phone", "")
        if phone:
            # Remove non-numeric characters except + for international
            cleaned = "".join(c for c in phone if c.isdigit() or c == "+")
            return cleaned
        return phone
