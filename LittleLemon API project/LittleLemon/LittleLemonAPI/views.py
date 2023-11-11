from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework import status, generics
from django.core.paginator import Paginator, EmptyPage
from rest_framework.permissions import IsAdminUser, IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User, Group
from .models import MenuItem, Cart, Order, OrderItem
from .serializers import MenuItemSerializer, UserSerializer, CartSerializer, UserViewSerializer, OrderSerializer, OrderItemSerializer
from .permissions import IsManager, IsDelivery

# Creates a new user with name, email and password
class UserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserViewSerializer


# Display current user 
class CurrentUserView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        return Response({"username":request.user.username, "email":request.user.email})
    
    
# Anyone can list menu items, only manager can create new menu item
class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    ordering_fields = ['price']
    search_fields = ['title']
    def get_permissions(self):
        if self.request.method == 'GET':
            # Allow any user to list (GET) menu items
            return [AllowAny()]  
        elif self.request.method =='POST':
            # Only Manager is able to add new menu item to menu
            return [IsManager()]
        else:
            return [IsAuthenticated()]

# Anyone can retrieve single menu item, only manager can put, patch, delete single menu item
class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer  
    def get_permissions(self):
        if self.request.method == 'GET':
            # Allow any user to retrieve (GET) the menu item
            return [AllowAny()]
        else:
            # For other methods (e.g., PUT and DELETE), check if the user is a manager
            return [IsManager()]


# Customer can list, create and delete the cart  
class CartListCreateDestroyView(APIView):
    permission_classes=[IsAuthenticated]
    def get(self, request):
        queryset = Cart.objects.get(user=request.user)
        serializer = CartSerializer(queryset)
        return Response(serializer.data, status=status.HTTP_200_OK)
    def post(self, request, *args, **kwargs):
        serializer = CartSerializer(data=request.data, context={'request': request})  # Pass the request object in the context
        serializer.is_valid(raise_exception=True)
        cart_item = serializer.save()
        return Response({"message": "Cart item created successfully", "cart_item_id": cart_item.id}, status=status.HTTP_201_CREATED)
    def delete(self, request):
        Cart.objects.all().delete()
        return Response({"message":"Menu items in cart deleted successfully"}, status=status.HTTP_200_OK)
    
    
# Manager can get the list of managers and add new manager to the list
class ManagerListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsManager]
    queryset = User.objects.all().filter(groups__name='Manager')
    serializer_class = UserViewSerializer

    def post(self, request, *args, **kwargs):
        user_serializer = self.get_serializer(data=request.data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        user.groups.add(Group.objects.get(name="Manager"))
        return Response({"message": "User added to Managers group successfully", "user_id": user.id}, status=status.HTTP_201_CREATED)


# Manager can remove user from manager group
class ManagerDeleteView(generics.DestroyAPIView):
    permission_classes = [IsManager]
    
    def delete(self, request, id):
        user = get_object_or_404(User, pk=id)
        managers_group = Group.objects.get(name="Manager")
        if managers_group.user_set.filter(pk=user.pk).exists():
            user.groups.remove(managers_group)
            return Response({"message": "User removed from the Manager group"}, status=status.HTTP_200_OK)
        else:
            return Response({"message":"User is not in the Manager group"}, status=status.HTTP_400_BAD_REQUEST)


# Manager can get the list of delivery crew and add new manager to the list
class DeliveryListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsManager]
    queryset = User.objects.all().filter(groups__name='Delivery crew')
    serializer_class = UserViewSerializer
    
    def post(self, request, *args, **kwargs):
        user_serializer = self.get_serializer(data=request.data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()
        user.groups.add(Group.objects.get(name="Delivery crew"))
        return Response({"message":"User added to Delivery crew group successfully", "user_id": user.id}, status = status.HTTP_201_CREATED)


# Manager can remove user from delivery crew group
class DeliveryDeleteView(generics.DestroyAPIView):
    permission_classes = [IsManager]
    
    def delete(self, request, id):
        user = get_object_or_404(User, pk=id)
        delivery_crew_group = Group.objects.get(name="Delivery crew")
        if delivery_crew_group.user_set.filter(pk=user.pk).exists():
            user.groups.remove(delivery_crew_group)
            return Response({"message": "User removed from the Delivery crew group"}, status=status.HTTP_200_OK)
        else:
            return Response({"message": "User is not in the Delivery crew group"}, status=status.HTTP_400_BAD_REQUEST)
            
# Manager can get the list of all orders, delivery gest the list where assigned, customer gets only its order.
# Customer can process to create new order by collecting data from the cart and it will be deleted
class OrderView(generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if IsManager().has_permission(request, self):
            queryset = Order.objects.all()
        elif IsDelivery().has_permission(request, self):
            queryset = Order.objects.filter(delivery_crew=request.user)
        else:
            queryset = Order.objects.filter(user=request.user)
        
        serializer = OrderSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        menuitem_count = Cart.objects.all().filter(user=self.request.user).count()
        if menuitem_count == 0:
            return Response({"message:": "no item in cart"})

        data = request.data.copy()
        total = self.get_total_price(self.request.user)
        data['total'] = total
        data['user'] = self.request.user.id
        order_serializer = OrderSerializer(data=data, context={'request': request})
        if (order_serializer.is_valid()):
            order = order_serializer.save()

            items = Cart.objects.all().filter(user=self.request.user).all()

            for item in items.values():
                orderitem = OrderItem(
                    order=order,
                    menuitem_id=item['menuitem_id'],
                    price=item['price'],
                    quantity=item['quantity'],
                )
                orderitem.save()

            Cart.objects.all().filter(user=self.request.user).delete() #Delete cart items

            result = order_serializer.data.copy()
            result['total'] = total
            return Response(result)
    
    def get_total_price(self, user):
        total = 0
        items = Cart.objects.all().filter(user=user).all()
        for item in items.values():
            total += item['price']
        return total


# Super Admin, Manager and Delivery Crew can update delivery_crew and status values
class SingleOrderView(generics.RetrieveUpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        if self.request.user.groups.count()==0: # Normal user, not belonging to any group = Customer
            return Response('Not Ok')
        else: #everyone else - Super Admin, Manager and Delivery Crew
            return super().update(request, *args, **kwargs)
