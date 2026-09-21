from django.forms import CharField, DateInput, Form, ModelForm, PasswordInput, Select, TextInput, Textarea

from main.models import Award, Experience


def action_key_field():
    return CharField(
        label="Action Key",
        strip=False,
        widget=PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Enter action key",
                "autocomplete": "current-password",
            }
        ),
    )


class AwardActionKeyForm(Form):
    action_key = action_key_field()


class AwardForm(ModelForm):
    action_key = action_key_field()
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

class ExperienceForm(ModelForm):
    action_key = action_key_field()

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
