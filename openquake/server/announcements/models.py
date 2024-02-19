from django.db import models


class Announcement(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    content = models.TextField()
    show = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.title}: {self.content}'
