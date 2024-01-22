from django.db import models


class Announcement(models.Model):
    title = models.CharField(max_length=100)
    content = models.TextField()

    def __str__(self):
        return f'{self.title}: {self.content}'
