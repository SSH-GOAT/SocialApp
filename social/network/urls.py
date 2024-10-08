"""
URL configuration for social_network project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from network.views import UsersView,FriendView,RequestView,BlockView,ProfileView
from rest_framework.routers import DefaultRouter

defaultRouter=DefaultRouter()
defaultRouter.register('user',UsersView)
defaultRouter.register('follow-request',RequestView)
defaultRouter.register('block',BlockView)
urlpatterns = [
    path('friends/', FriendView.as_view(), name='friends-list'),
    path('profile/<str:pk>/', ProfileView.as_view({'get': 'retrieve', 'put': 'update'}), name='user-profile'),
]+defaultRouter.urls
