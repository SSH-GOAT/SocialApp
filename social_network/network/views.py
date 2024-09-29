from django.shortcuts import render
from django_filters import rest_framework as filters
from network.filter import UserFilter
from django.core.cache import cache
from django.db import transaction
from .permission import AdminPermission
from rest_framework import status,serializers
from network.models import User,Blocked,FriendRequest
from network.serializers import UserSerializer,RequestSerailizer,UserSignupSerializer,BlockSerializer
from rest_framework import viewsets,mixins,views,generics
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication,BasicAuthentication,SessionAuthentication,BaseAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
# class CustomPagination(PageNumberPagination):
#     page_size_query_param = 'page_size'  # Allow clients to set page size
#     max_page_size = 10  # Maximum number of items per page

class SignupView(generics.CreateAPIView):
    queryset=User.objects.all()
    serializer_class=UserSignupSerializer

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
    

class FriendView(generics.ListAPIView):
    # def get_queryset(self):
    #     return self.request.user.friends.all()
    
    # queryset=User.objects.only('friends')
    authentication_classes = [TokenAuthentication]
    permission_classes=[IsAuthenticated]
    serializer_class=UserSerializer
    def list(self, request, *args, **kwargs):
        return Response(request.user.friends.all())
    
class RequestView(viewsets.ModelViewSet):
    RATE_LIMIT = 3  # Allow 3 requests
    RATE_LIMIT_PERIOD = 60  # Within 60 seconds
    serializer_class=RequestSerailizer
    queryset=FriendRequest.objects.all()
    pagination_class=None
    authentication_classes = [TokenAuthentication]
    permission_classes=[IsAuthenticated]
    def get_queryset(self):
        current_user = self.request.user  # Get the currently authenticated user
        return self.queryset.filter(requestBy__email=current_user.email) 
    def get_serializer_context(self):
        # Pass the current user to the serializer context
        context = super().get_serializer_context()
        context['current_user'] = self.request.user
        print(context,'cost')
        return context
    def perform_create(self, serializer):
        blockers = Blocked.objects.filter(blockedUser=self.request.user)
        print(blockers,'blockers')
        print(serializer.validated_data['requestTo'].email,'email')
        li = [blocked.blockedBy.email for blocked in blockers]
        if(serializer.validated_data['requestTo'].email in li):
            raise serializers.ValidationError(f"you have blocked by {serializer.validated_data['requestTo']}")
        return super().perform_create(serializer)
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        user_id = request.user.email
        cache_key = f"user#{user_id}_sending_frnd_req"

        # Get the current request count
        request_count = cache.get(cache_key, 0)

        if request_count >= self.RATE_LIMIT:
            return Response(
                {"error": "Rate limit exceeded. Please try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        response=super().create(request, *args, **kwargs)
        cache.set(cache_key, request_count + 1, timeout=self.RATE_LIMIT_PERIOD)
        return response
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
    
    
class BlockView(viewsets.GenericViewSet,mixins.CreateModelMixin,mixins.ListModelMixin,mixins.DestroyModelMixin,mixins.RetrieveModelMixin):
    authentication_classes = [TokenAuthentication]
    permission_classes=[IsAuthenticated]
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
    permission_classes=[IsAuthenticated,AdminPermission]
    serializer_class=UserSerializer
    pagination_class=None
    queryset=User.objects.all()
    def perform_update(self, serializer):
        email = self.kwargs.get('pk')
        if(email!=self.request.user.email and (not self.request.user.is_superuser)):
            serializers.ValidationError("cannot modiy others data")
        return super().perform_update(serializer)
    
    