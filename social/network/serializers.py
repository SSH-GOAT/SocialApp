from rest_framework import serializers
from datetime import date
from django.db import IntegrityError
from django.utils import timezone
from rest_framework.response import Response
from rest_framework import status
from network.models import User,FriendRequest,Blocked
from django.contrib.auth.hashers import make_password

class BlockSerializer(serializers.ModelSerializer):
    blockedBy=serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model=Blocked
        fields='__all__'


class UserSerializer(serializers.ModelSerializer):
    friends=serializers.PrimaryKeyRelatedField(many=True,read_only=True)
    class Meta:
        model = User
        exclude=('password','groups','user_permissions')
class FriendsSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        exclude=('password','groups','user_permissions')

class UserSignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
    style={'input_type': 'password'},write_only=True
)
    class Meta:
        model=User
        fields=("email","name","password")
    
    def create(self, validated_data):
        # Encrypt the password using make_password
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)
      
class RequestSerailizer(serializers.ModelSerializer):
    requestBy=serializers.StringRelatedField(read_only=True)
    requestSentOn=serializers.DateTimeField(read_only=True)
    def validate_requestSentOn(self, value):
        if value < timezone.now():
            raise serializers.ValidationError("time travel not possible")
        return value
    def __init__(self, *args, **kwargs):
        current_user = kwargs['context'].pop('current_user', None)
        super(RequestSerailizer, self).__init__(*args, **kwargs)
        if current_user:
            self.fields['requestTo'].queryset = User.objects.exclude(email=current_user.email).all()
    class Meta:
        model=FriendRequest
        fields="__all__"
    def create(self, validated_data):
        request = self.context['request']
        validated_data['requestBy'] = request.user 
        try:
            return super().create(validated_data)
        except IntegrityError  as e:
            return Response(
                {"error": "Database integrity error occurred. Please try again later."},
                status=status.HTTP_400_BAD_REQUEST
            )

class UpdateRequestSerailizer(serializers.ModelSerializer):
    requestBy=serializers.StringRelatedField(read_only=True)
    status=serializers.CharField(read_only=True)
    def __init__(self, *args, **kwargs):
        current_user = kwargs['context'].pop('current_user', None)
        super(RequestSerailizer, self).__init__(*args, **kwargs)
        if current_user:
            self.fields['requestTo'].queryset = User.objects.exclude(email=current_user.email).all()
    class Meta:
        model=FriendRequest
        fields="__all__"