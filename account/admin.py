from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Account, Instance, Profile, User

admin.site.register(Account)
admin.site.register(Instance)
admin.site.register(Profile)

admin.site.register(User, UserAdmin)
