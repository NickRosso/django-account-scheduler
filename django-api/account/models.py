from django.db import models


class Account(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    last_synchronized = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.last_synchronized)