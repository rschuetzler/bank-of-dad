from django.contrib import admin

from .models import Account, InterestBreakpoint, InterestScheme, Transaction


# Register your models here.
@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ("owner", "balance", "accrued_interest", "next_month_interest")


admin.site.register(Transaction)

admin.site.register(InterestScheme)


@admin.register(InterestBreakpoint)
class BreakpointAdmin(admin.ModelAdmin):
    list_display = (
        "balance_breakpoint",
        "annual_interest_rate",
        "monthly_interest_rate",
    )
