from django.contrib import admin

from .models import Account, InterestBreakpoint, InterestScheme, Transaction

# Register your models here.
admin.site.register(Account)
admin.site.register(Transaction)

admin.site.register(InterestScheme)
admin.site.register(InterestBreakpoint)
