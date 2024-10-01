from builtins import ValueError, dict, zip
from django.utils import timezone
from django.db import models
from enum import Enum
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager,PermissionsMixin


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, name, password, **extra_fields):
        values = [email, name]
        field_value_map = dict(zip(self.model.REQUIRED_FIELDS, values))
        for field_name, value in field_value_map.items():
            if not value:
                raise ValueError('The {} value must be set'.format(field_name))

        email = self.normalize_email(email)
        user = self.model(
            email=email,
            name=name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, name, password=None, **extra_fields):
        return self._create_user(email, name, password, **extra_fields)

    def create_superuser(self, email, name, password=None, **extra_fields):
        return self._create_user(email, name, password, **extra_fields)

class RequestStatus(Enum):
    SENT = 'sent'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'



# Create your models here.
class User(AbstractBaseUser,PermissionsMixin):
    email=models.EmailField(unique=True,primary_key=True)
    name=models.CharField(max_length=40)
    dateJoined = models.DateTimeField(default=timezone.now)
    friends=models.ManyToManyField('self')
    objects=UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'password']

    def __str__(self) -> str:
        return self.email
class Blocked(models.Model):
    blockedBy=models.ForeignKey(User,null=False,on_delete=models.CASCADE)
    blockedUser=models.ForeignKey(User,null=False,on_delete=models.CASCADE,related_name="myBlockList")
    class Meta:
        unique_together = ('blockedBy', 'blockedUser')

class FriendRequest(models.Model):
    requestBy=models.ForeignKey(User,models.CASCADE,related_name='request_sent')
    status=models.CharField(max_length=8, choices=[(status.value, status.name) for status in RequestStatus],default=RequestStatus.SENT.value)
    requestTo=models.ForeignKey(User,models.CASCADE,related_name='request_received')
    updatedAt = models.DateTimeField(auto_now=True)
    requestSentOn = models.DateTimeField(default=timezone.now)
    class Meta:
        unique_together = ('requestBy', 'requestTo')  

    def __str__(self) -> str:
        return self.requestBy.email+' -> '+ self.requestTo.email

