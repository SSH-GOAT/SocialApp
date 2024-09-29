from rest_framework import serializers
from django.db import IntegrityError
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
    # request_to=serializers.StringRelatedField(queryset=)
    def __init__(self, *args, **kwargs):
        # Get the current user from the context
        current_user = kwargs['context'].pop('current_user', None)
        super(RequestSerailizer, self).__init__(*args, **kwargs)
        if current_user:
            self.fields['requestTo'].queryset = User.objects.exclude(email=current_user.email).all()
        
        # If a current user is provided, exclude them from the queryset
    status=serializers.CharField(read_only=True)
    class Meta:
        model=FriendRequest
        fields="__all__"
    def create(self, validated_data):
        request = self.context['request']  # Access the request context
        validated_data['requestBy'] = request.user 
        try:
            return super().create(validated_data)
        except IntegrityError  as e:
            return Response(
                {"error": "Database integrity error occurred. Please try again later."},
                status=status.HTTP_400_BAD_REQUEST
            )
    def update(self, instance, validated_data):
        return super().update(instance, validated_data)