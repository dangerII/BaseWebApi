from django.db import models
from django.urls import reverse
from datetime import datetime, timedelta
from django.core.validators import RegexValidator, MinLengthValidator
import os
from django.utils.translation import gettext_lazy as _

# Create your models here.


def user_directory_path(instance, filename: str):
    ext = filename.split('.').pop()
    filename = '{0}_{1}.{2}'.format(instance.id, instance.User_name, ext)
    return filename  # 系统路径分隔符差异，增强代码重用性
    
def upload_directory_path(instance, filename: str):
    ext = filename.split('.').pop()
    time = datetime.now()
    filename = '{0}_{1}.{2}'.format(instance.id, time.strftime('%H_%M_%S'), ext)
    dirname = time.strftime('%Y_%m_%d')
    return os.path.join('message_pic', dirname, filename) # 系统路径分隔符差异，增强代码重用性

# Create your models here.
class User(models.Model):
    QQ_number = [RegexValidator(r'^[0-9]*$', 'Only 0-9 are allowed.'), MinLengthValidator(5, message='Too short')]
    Phone_number = [RegexValidator(r'^[+]?[0-9]*$', 'Only 0-9 are allowed.'), MinLengthValidator(10, message='Too short')]

    id = models.AutoField(primary_key = True)
    User_name = models.CharField(max_length = 20)
    Password =models.CharField('Password', max_length = 128, serialize = False)
    E_Mail = models.EmailField(max_length = 50, verbose_name = "e-mail", unique = True, editable = False)
    Gender = models.CharField('Sex', max_length = 6, choices = [('male', 'Male'), ('female', 'Famale'), ('secret', 'Secret')], default = 'secret')
    BirthDay = models.DateField('Birthday', null = True, blank = True)
    Profile_Pic = models.ImageField('Avatar', upload_to = user_directory_path, default = 'default/user.jpg')
    QQ = models.CharField('QQ Number', max_length = 11, null = True, blank =True, validators = QQ_number)
    Telephone = models.CharField("Telephone", max_length = 14, null = True, blank =True, validators = Phone_number)
    Describe = models.CharField('Describe', max_length = 128, null = True, blank = True)
    Ctime = models.DateTimeField(auto_now_add = True, verbose_name = "Register Time")
    Last_Login = models.DateTimeField(default = datetime.now)
    Last_Update = models.DateTimeField(auto_now=True)
    Secret = models.CharField('Secret_Field', max_length = 40, null = True, blank = True)
    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self):
        return self.User_name

    def get_absolute_url(self):
        return reverse("_detail", kwargs={"pk": self.pk})

    def natural_key(self):
        return self.User_name, self.id

class UserToken(models.Model):
    user = models.OneToOneField(to = 'User', unique = True, on_delete = models.CASCADE)
    token = models.CharField(max_length = 64, verbose_name = "User token")
    expiration_time = models.DateTimeField(default = datetime.now, verbose_name = "expiration time")
    add_time = models.DateTimeField(auto_now_add = True, verbose_name = "create time")

    def __str__(self):
        return self.token


class UploadImage(models.Model):
    id = models.AutoField(primary_key = True)
    image = models.ImageField('Avatar', upload_to = upload_directory_path)