from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class Newspaper(models.Model):
    title = models.CharField(max_length=256)
    content = models.TextField()
    publish_date = models.DateTimeField()
    topics = models.ManyToManyField('Topic', related_name='newspapers')
    publishers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='newspapers'
    )

    class Meta:
        ordering = ['-publish_date', 'title']

    def get_absolute_url(self):
        return reverse(
            'agency:newspaper-detail',
            kwargs={'pk': self.pk},
        )

    def __str__(self):
        return self.title


class Topic(models.Model):
    name = models.CharField(max_length=256, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Redactor(AbstractUser):
    years_of_experience = models.IntegerField(null=True, blank=True)

    class Meta:
        verbose_name = 'redactor'
        verbose_name_plural = 'redactors'

    def get_absolute_url(self):
        return reverse(
            'agency:redactor-detail',
            kwargs={'pk': self.pk},
        )

    def __str__(self):
        return f'{self.username} ({self.first_name} {self.last_name}, {self.years_of_experience} years of experience)'
