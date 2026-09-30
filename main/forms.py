from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.forms import CharField, DateInput, ModelForm, PasswordInput, Select, TextInput, Textarea
from django.contrib.auth.models import User
from django.utils.html import strip_tags
from urllib.parse import urlsplit

from main.models import Award, Experience


class UserUpdateForm(ModelForm):
    current_password = CharField(
        label="Current password",
        strip=False,
        widget=PasswordInput(attrs={"class": "form-control", "autocomplete": "current-password"}),
    )
    new_password = CharField(
        label="New password",
        required=False,
        strip=False,
        help_text="Leave blank to keep your current password.",
        widget=PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )
    confirm_new_password = CharField(
        label="Confirm new password",
        required=False,
        strip=False,
        widget=PasswordInput(attrs={"class": "form-control", "autocomplete": "new-password"}),
    )

    class Meta:
        model = User
        fields = ["username"]

        labels = {
            "username": "Username",
        }

        widgets = {
            "username": TextInput(
                attrs={"class": "form-control", "placeholder": "Enter username"}
            ),
        }

    def clean_current_password(self):
        password = self.cleaned_data["current_password"]
        if not self.instance.check_password(password):
            raise ValidationError("Current password is incorrect")
        return password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_new_password")
        if new_password != confirm_password:
            self.add_error("confirm_new_password", "New passwords do not match")
        elif new_password:
            validate_password(new_password, self.instance)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data["new_password"]:
            user.set_password(self.cleaned_data["new_password"])
        if commit:
            user.save()
        return user


class AwardForm(ModelForm):
    thumbnail = CharField(
        max_length=255,
        required=False,
        label="Thumbnail Path or URL",
        widget=TextInput(
            attrs={
                "class": "form-control",
                "placeholder": "/static/img/award.jpeg or https://...",
            }
        ),
        help_text="Use a relative path such as /static/img/award.jpeg or an external URL.",
    )

    class Meta:
        model = Award
        fields = [
            "title",
            "description",
            "thumbnail",
            "issuer",
            "date_received",
        ]

        labels = {
            "title": "Title",
            "description": "Description",
            "thumbnail": "Thumbnail URL",
            "issuer": "Issuer",
            "date_received": "Date Received",
        }

        widgets = {
            "title": TextInput(
                attrs={"class": "form-control", "placeholder": "Enter title"}
            ),
            "description": Textarea(
                attrs={"class": "form-control", "placeholder": "Enter description"}
            ),
            "issuer": TextInput(
                attrs={"class": "form-control", "placeholder": "Enter issuer"}
            ),
            "date_received": DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                    "placeholder": "Enter date received",
                }
            ),
        }

    def clean_title(self):
        title = strip_tags(self.cleaned_data["title"]).strip()
        if not title:
            raise ValidationError("Award title can't contain only HTML tags.")
        return title

    def clean_description(self):
        return strip_tags(self.cleaned_data.get("description") or "").strip()

    def clean_issuer(self):
        return strip_tags(self.cleaned_data.get("issuer") or "").strip()

    def clean_thumbnail(self):
        thumbnail = strip_tags(self.cleaned_data.get("thumbnail") or "").strip()
        if not thumbnail:
            return thumbnail

        if thumbnail.startswith("/") and not thumbnail.startswith("//") and "\\" not in thumbnail:
            return thumbnail

        try:
            parsed_url = urlsplit(thumbnail)
        except ValueError as error:
            raise ValidationError("Use a /static/... path or an http(s) URL.") from error

        if parsed_url.scheme.lower() not in {"http", "https"} or not parsed_url.netloc:
            raise ValidationError("Use a /static/... path or an http(s) URL.")

        return thumbnail

class ExperienceForm(ModelForm):
    class Meta:
        model = Experience
        fields = [
            "title",
            "description",
            "category",
            "keyfeatures",
            "start_at",
            "ended_at",
        ]

        labels = {
            "title": "Title",
            "description": "Description",
            "category": "Category",
            "keyfeatures": "Key Features",
            "start_at": "Start Date",
            "ended_at": "End Date",
        }

        widgets = {
            "title": TextInput(
                attrs={"class": "form-control", "placeholder": "Enter title"}
            ),
            "description": Textarea(
                attrs={"class": "form-control", "placeholder": "Enter description"}
            ),
            "category": Select(
                attrs={"class": "form-control"}
            ),
            "keyfeatures": Textarea(
                attrs={
                    "class": "form-control",
                    "placeholder": 'Enter key features as a JSON array, e.g. ["Feature 1", "Feature 2"]',
                }
            ),
            "start_at": DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                    "placeholder": "Enter start date",
                }
            ),
            "ended_at": DateInput(
                attrs={
                    "class": "form-control",
                    "type": "date",
                    "placeholder": "Enter end date",
                }
            ),
        }

    def clean_title(self):
        title = strip_tags(self.cleaned_data["title"]).strip()
        if not title:
            raise ValidationError("Experience title can't contain only HTML tags.")
        return title

    def clean_description(self):
        return strip_tags(self.cleaned_data.get("description") or "").strip()

    def clean_keyfeatures(self):
        keyfeatures = self.cleaned_data.get("keyfeatures")
        if keyfeatures in (None, ""):
            return []
        if not isinstance(keyfeatures, list):
            raise ValidationError("Key features must be a JSON array of text values.")

        cleaned_keyfeatures = []
        for keyfeature in keyfeatures:
            if not isinstance(keyfeature, str):
                raise ValidationError("Each key feature must be text.")
            cleaned_keyfeature = strip_tags(keyfeature).strip()
            if cleaned_keyfeature:
                cleaned_keyfeatures.append(cleaned_keyfeature)
        return cleaned_keyfeatures
