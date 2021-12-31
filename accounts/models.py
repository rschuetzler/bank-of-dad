from django.contrib.auth import get_user_model
from django.db import models
from django_extensions.db.models import TimeStampedModel

User = get_user_model()


# Create your models here.
class Account(TimeStampedModel):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    responsible_person = models.ManyToManyField(User, related_name="responsible_person")
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    interest_scheme = models.ForeignKey(
        "InterestScheme", on_delete=models.CASCADE, null=True, blank=True
    )
    upcoming_interest = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.owner}'s account: ${self.balance}"

    # Daily interest calculation, going into an "upcoming interest" field
    # Monthly the upcoming interest is added to the balance and reset to 0

    def calculate_interest(self):
        if not self.interest_scheme:
            return 0
        else:
            pass


class Transaction(TimeStampedModel):
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(max_length=255)

    class TransactionTypes(models.TextChoices):
        deposit = "deposit", "Deposit"
        withdraw = "withdraw", "Withdraw"
        interest = "interest", "Interest"

    transaction_type = models.CharField(
        max_length=10,
        choices=TransactionTypes.choices,
        default=TransactionTypes.deposit,
    )
    transaction_date = models.DateField()

    def __str__(self):
        return f"{self.account}: {self.transaction_type} of ${self.amount} on {self.transaction_date}"

    def save(self, *args, **kwargs):
        if self.transaction_type == "deposit" or self.transaction_type == "interest":
            self.account.balance += self.amount
        elif self.transaction_type == "withdraw":
            self.account.balance -= self.amount

        else:
            raise ValueError("Invalid transaction type")
        self.account.save()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.transaction_type == "deposit" or self.transaction_type == "interest":
            self.account.balance -= self.amount
        elif self.transaction_type == "withdraw":
            self.account.balance += self.amount
        self.account.save()
        super().delete(*args, **kwargs)


# class Goal(TimeStampedModel):
#     account = models.ForeignKey(Account, on_delete=models.CASCADE)
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     description = models.TextField(max_length=255)
#     goal_date = models.DateField()
#     reward = models.DecimalField(max_digits=10, decimal_places=2)


class InterestScheme(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    max_interest_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True
    )


class InterestBreakpoint(models.Model):
    interest_scheme = models.ForeignKey(InterestScheme, on_delete=models.CASCADE)
    balance_breakpoint = models.DecimalField(max_digits=10, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=10, decimal_places=2)
