from django.contrib import admin
from .models import UploadImage, User, UserToken

# Register your models here.

admin.site.register(User)
admin.site.register(UserToken)
admin.site.register(UploadImage)
