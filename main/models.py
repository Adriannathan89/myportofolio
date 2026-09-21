from django.db import models
from django.utils import timezone
import uuid

# Create your models here.
class Experience(models.Model):
    EXPERIENCE_ENUM = [
        ("internship", "Internship"),
        ("research", "Research"),
        ("volunteer", "Volunteer"),
        ("part-time", "Part-Time"),
        ("full-time", "Full-Time"),
        ("freelance", "Freelance"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=EXPERIENCE_ENUM, default="freelance")
    keyfeatures = models.JSONField(blank=True, null=True)
    start_at = models.DateField(blank=True, null=True)
    ended_at = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)
    updated_at = models.DateTimeField(default=timezone.now, blank=True, null=True)

    def __str__(self):
        return self.title


    @property
    def is_ongoing(self):
        return self.ended_at is  None

class Award(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    thumbnail = models.CharField(max_length=255, blank=True, null=True)
    issuer = models.CharField(max_length=255, blank=True, null=True)
    date_received = models.DateField()

    def __str__(self):
        return self.title
