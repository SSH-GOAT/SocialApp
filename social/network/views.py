from django.shortcuts import render
from django_filters import rest_framework as filters
from django.db.models import Q
from network.filter import UserFilter
from datetime import timedelta
from django.utils import timezone
from django.db import IntegrityError
from django.core.cache import cache
from django.db import transaction
from .permission import AdminPermission
from rest_framework import status,serializers
from network.models import User,Blocked,FriendRequest
from network.serializers import UserSerializer,RequestSerailizer,UserSignupSerializer,BlockSerializer,UpdateRequestSerailizer
from rest_framework import viewsets,mixins,views,generics
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication,BaseAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
import logging

logger = logging.getLogger('social_network')

class SignupView(generics.CreateAPIView):
    queryset=User.objects.all()
    serializer_class=UserSignupSerializer
    def create(self, request, *args, **kwargs):
        logger.debug(f"Creating MyModel object with data: {request.data}")
        response = super().create(request, *args, **kwargs)
        logger.debug(f"Created object with ID: {response.data}")
        return response

# Create your views here.
class UsersView( mixins.ListModelMixin,
                                # mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    
    queryset = User.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    authentication_classes = [ TokenAuthentication]
    permission_classes=[IsAuthenticated]
    pagination_class=PageNumberPagination
    page_size=10
    filterset_class = UserFilter
    serializer_class = UserSerializer
    def list(self, request, *args, **kwargs):
        logger.debug("Listing MyModel objects")
        response = super().list(request, *args, **kwargs)
        logger.debug(f"Response: {response.data}")
        return response
    

class FriendView(generics.ListAPIView):
    def get_queryset(self):
        return self.request.user.friends.all()
    
    authentication_classes = [ TokenAuthentication]
    permission_classes=[IsAuthenticated,AdminPermission]
    serializer_class=UserSerializer
    def list(self, request, *args, **kwargs):
        logger.debug("Listing MyModel objects")
        friends = request.user.friends.exclude(email=request.user.email).all()
        # Serialize the friends
        serializer = UserSerializer(friends, many=True)
        logger.debug(f"Created object with ID: {serializer.data}")
        return Response(serializer.data)
        # return Response(UserSerializer(request.user.friends.all(),many=True))
    
class RequestView(viewsets.ModelViewSet):
    RATE_LIMIT = 3  # Allow 3 requests
    RATE_LIMIT_PERIOD = 60  # Within 60 seconds
    serializer_class=RequestSerailizer
    queryset=FriendRequest.objects.all()
    pagination_class=None
    authentication_classes = [TokenAuthentication]
    permission_classes=[IsAuthenticated,AdminPermission]
    def get_queryset(self):
        current_user = self.request.user  # Get the currently authenticated user
        return self.queryset.filter(Q(requestBy__email=current_user.email) | Q(requestTo__email=current_user.email) ) 
    def get_serializer_context(self):
        # Pass the current user to the serializer context
        context = super().get_serializer_context()
        context['current_user'] = self.request.user
        return context
    def perform_create(self, serializer):
        blockers = Blocked.objects.filter(blockedUser=self.request.user)
        li = [blocked.blockedBy.email for blocked in blockers]
        if(serializer.validated_data['status'] in ['rejected','accepted']):
            raise serializers.ValidationError(f"cannot create a follow request with {serializer.validated_data['status']} status")
        if(serializer.validated_data['requestTo'].email in li):
            raise serializers.ValidationError(f"you have blocked by {serializer.validated_data['requestTo']}")
        try:
            response= super().perform_create(serializer)
        except IntegrityError as e:
            logger.error(f"updating the follow request")
            return self.perform_update_after_creation(serializer)
        return response
    def perform_update_after_creation(self, instance):
        # Your update logic here
        # For example, modifying a field or performing some action
        found_instance=FriendRequest.objects.filter(requestTo=instance.validated_data['requestTo'],requestBy=instance.validated_data['requestBy']).first()
        if(found_instance.updatedAt>timezone.now()-timedelta(hours=24)):
            raise serializers.ValidationError(f"recent follow request has been reject, kindly wait for 24 hours")
        
        instance.validated_data['status'] = 'sent'
        return instance.save()
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        user_id = request.user.email
        cache_key = f"user#{user_id}_sending_frnd_req"

        # Get the current request count
        request_count = cache.get(cache_key, 0)

        if request_count >= self.RATE_LIMIT:
            return Response(
                {"error": "Wait for another 60 seconds before sending a follow request"},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        logger.debug(f"Creating MyModel object with data: {request.data}")
        response=super().create(request, *args, **kwargs)
        cache.set(cache_key, request_count + 1, timeout=self.RATE_LIMIT_PERIOD)
        logger.debug(f"Created object with ID: {response.data}")
        return response
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        logger.debug(f"Updating MyModel object with ID: {kwargs['pk']} with data: {request.data}")
        response = super().update(request, *args, **kwargs)
        logger.debug(f"Updated object with ID: {response.data}")
        return response
    
    @transaction.atomic
    def perform_update(self, serializer):
        # if(serializer.validated_data['requestBy']==self.request.user.email):
        if(serializer.validated_data['status']=='accepted'):
            current_user=self.request.user
            current_user.friends.add(serializer.validated_data['requestBy'])
            current_user.save()
            return Response("follow request accepted, user added to friend list")
        try:
            saved=serializer.save()
        except IntegrityError as e:
            logger.error(f"user {self.request.user.email} trying to send another request")
            raise serializers.ValidationError("kindly wait for the user to accept the follow request")
        return saved

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        logger.debug(f"Deleting MyModel object with ID: {kwargs['pk']}")
        response = super().destroy(request, *args, **kwargs)
        logger.debug(f"Deleted object with ID: {kwargs['pk']}")
        return response
    
    
class BlockView(viewsets.GenericViewSet,mixins.CreateModelMixin,mixins.ListModelMixin,mixins.DestroyModelMixin,mixins.RetrieveModelMixin):
    authentication_classes = [TokenAuthentication]
    permission_classes=[IsAuthenticated,AdminPermission]
    serializer_class=BlockSerializer
    pagination_class=None
    queryset=Blocked.objects.all()
    def get_queryset(self):
        current_user = self.request.user  # Get the currently authenticated user
        return self.queryset.filter(blockedBy__email=current_user.email) 
    def get_object(self):
        queryset = self.get_queryset()
        obj = queryset.get(pk=self.kwargs['pk'])  # Get the object using the primary key from the URL
        if(obj.blockedBy!=self.request.user.email and (not self.request.user.is_superuser)):
            serializers.ValidationError("don't have permission")
        return obj
    def perform_create(self, serializer):
        return serializer.save(blockedBy=self.request.user)
    
class ProfileView(mixins.RetrieveModelMixin,
                       mixins.UpdateModelMixin,
                       viewsets.GenericViewSet):
    authentication_classes = [TokenAuthentication]
    permission_classes=[IsAuthenticated]
    serializer_class=UserSerializer
    pagination_class=None
    queryset=User.objects.all()
    
    def perform_update(self, serializer):
        email = self.kwargs.get('pk')
        if(email!=self.request.user.email and (not self.request.user.is_superuser)):
            serializers.ValidationError("cannot modiy others data")
        return super().perform_update(serializer)
