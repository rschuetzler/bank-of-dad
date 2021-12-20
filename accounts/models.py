from django.contrib.auth import get_user_model
from django.db import models
from django_extensions.db.models import TimeStampedModel

User = get_user_model()


# Create your models here.
class Account(TimeStampedModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    responsible_person = models.ManyToManyField(User, related_name="responsible_person")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)


class Transaction(TimeStampedModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(max_length=255)
    transaction_type = models.CharField(max_length=10)
    transaction_date = models.DateField()


# class Goal(TimeStampedModel):
#     account = models.ForeignKey(Account, on_delete=models.CASCADE)
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     description = models.TextField(max_length=255)
#     goal_date = models.DateField()
#     reward = models.DecimalField(max_digits=10, decimal_places=2)
