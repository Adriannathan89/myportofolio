from django.forms import CharField, DateInput, ModelForm, TextInput, Textarea

from main.models import Award


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
