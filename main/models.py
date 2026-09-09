from django.db import models
import uuid

# Create your models here.
class Experience(models.Model):
    EXPERIENCE_ENUM = [
        ("internship", "Internshipo"),
        ("reseach", "Research"),
        ("volunteer", "Volunteer"),
        ("part-time", "Part-Time"),
        ("full-time", "Full-Time"),
        ("freelance", "Freelance"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.CharField(max_length=20, choices=EXPERIENCE_ENUM, default="freelance")
    thumbnail = models.URLField(max_length=255, blank=True, null=True)
    start_at = models.DateField(auto_now_add=True)
    ended_at = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.title


    @property
    def is_ongoing(self):
        return self.ended_at is  None