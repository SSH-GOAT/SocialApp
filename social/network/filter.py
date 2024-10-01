from django_filters import rest_framework as filters
from .models import User

class UserFilter(filters.FilterSet):
    email = filters.CharFilter(lookup_expr='exact')  # Filter for keyword matches the exact email
    name = filters.CharFilter(lookup_expr='icontains')  # Filter for keyword contains any part of the name

    class Meta:
        model = User
        fields = ['email', 'name']
