from django.contrib.auth.models import AbstractUser
from django.db import models

class Newspaper(models.Model):
    title = models.CharField(max_length=256)
    content = models.TextField()
    publish_date = models.DateTimeField()
    topics = models.ManyToManyField("Topic", related_name="newspapers")
    publishers = models.ManyToManyField("Redactor", related_name="newspapers")

    class Meta:
        ordering = ['-publish_date', 'title']

    def __str__(self):
        return self.title


class Topic(models.Model):
    name = models.CharField(max_length=256)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Redactor(AbstractUser):
    years_of_experience = models.IntegerField()

    class Meta:
        verbose_name = 'redactor'
        verbose_name_plural = 'redactors'

    def __str__(self):
        return f"{self.username} ({self.first_name} {self.last_name}, {self.years_of_experience} years of experience)"
