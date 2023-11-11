from django.contrib.auth.models import User, Group
from rest_framework.permissions import IsAdminUser, IsAuthenticated

class IsManager(IsAuthenticated):
    def has_permission(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            if user.groups.filter(name="Manager"):
                return True
        return False
    
class IsDelivery(IsAuthenticated):
    def has_permission(self, request, *args, **kwargs):
        user = request.user
        if user.is_authenticated:
            if user.groups.filter(name="Delivery crew").exists():
                return True
        return False