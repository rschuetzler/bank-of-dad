import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from dateutil import relativedelta
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
    accrued_interest = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    last_interest_accrued = models.DateTimeField(
        auto_now_add=True, blank=False, null=False
    )
    historical_interest = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )

    def __str__(self):
        return f"{self.owner}'s account: ${self.balance}"

    # Daily interest calculation, going into an "upcoming interest" field
    # Monthly the upcoming interest is added to the balance and reset to 0

    # def calculate_interest(self):
    #     now = datetime.now()
    #     period = (now - self.last_interest_accrued) / timedelta(days=365)
    #     balance = self.balance + self.accrued_interest

    #     if not self.interest_scheme or self.balance == 0:
    #         return 0
    #     else:
    #         previous_breakpoint = 0
    #         total = 0

    #         for breakpoint in self.interest_scheme.breakpoints:
    #             if balance > breakpoint.balance_breakpoint:
    #                 interest = (balance - previous_breakpoint) * math.e ** (
    #                     breakpoint.annual_interest_rate * period
    #                 )
    #                 total += interest
    #                 previous_breakpoint = breakpoint.balance_breakpoint
    #         return total

    def calculate_interest(self, to_date=datetime.now(timezone.utc)):
        balance = self.balance + self.accrued_interest

        period = (to_date - self.last_interest_accrued) / timedelta(days=365)

        if not self.interest_scheme or self.balance == 0:
            return 0
        # elif period < timedelta(days=1):
        #     return 0
        else:
            previous_breakpoint = 0
            total = 0

            for breakpoint in self.interest_scheme.breakpoints.all():
                if balance > previous_breakpoint:
                    interest = float(balance - previous_breakpoint) * math.pow(
                        math.e, float(breakpoint.annual_interest_rate) * period
                    )
                    total += interest - float(balance - previous_breakpoint)
                    previous_breakpoint = breakpoint.balance_breakpoint
            return total

    def accrue_interest(self):
        interest = self.calculate_interest(datetime.now(timezone.utc))

        if interest > 0:
            self.accrued_interest += interest
            self.last_interest_accrued = datetime.now(timezone.utc)
            self.save()

    def pay_interest(self):
        self.accrue_interest()
        deposit = Transaction(
            account=self,
            amount=self.accrued_interest,
            transaction_type=Transaction.TransactionTypes.interest,
            description="Interest payment",
        )
        deposit.save()

    @property
    def next_month_interest(self):
        today = datetime.now(timezone.utc)

        # This is terrible, but it reliably gets me the first of next month
        next_month = today.replace(day=28)
        next_month += timedelta(days=7)
        first = next_month.replace(day=1)

        return f"${self.calculate_interest(first):.2f}"


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
    transaction_date = models.DateField(auto_now_add=True)

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

    def __str__(self):
        return f"{self.owner}'s interest scheme with "


class InterestBreakpoint(models.Model):
    interest_scheme = models.ForeignKey(
        InterestScheme, on_delete=models.CASCADE, related_name="breakpoints"
    )
    balance_breakpoint = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    annual_interest_rate = models.DecimalField(
        max_digits=20, decimal_places=10, default=0
    )

    def __str__(self):
        return f"{self.interest_scheme}: {self.balance_breakpoint} with {self.annual_interest_rate}%"

    @property
    def daily_interest_rate(self):
        return math.pow(1 + self.annual_interest_rate, (1 / 365)) - 1

    @property
    def monthly_interest_rate(self):
        return math.pow(1 + self.annual_interest_rate, (1 / 12)) - 1

    class Meta:
        ordering = ["balance_breakpoint"]
