from rest_framework import serializers 
from .models import  MenuItem, Category, Cart, Order, OrderItem
from rest_framework.validators import UniqueTogetherValidator 
from django.contrib.auth.models import User
 

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']
 
class MenuItemSerializer(serializers.ModelSerializer):
    validators = [
        UniqueTogetherValidator(queryset=MenuItem.objects.all(), fields=['title', 'price']),
    ]
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category', 'category']
    
class CartSerializer(serializers.ModelSerializer):
    menuitem_id = serializers.PrimaryKeyRelatedField(queryset=MenuItem.objects.all(), source='menuitem', write_only=True)
    menuitem = MenuItemSerializer(read_only=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
        
    class Meta:
        model = Cart
        fields = ['user', 'menuitem_id', 'menuitem', 'unit_price', 'quantity', 'price']
        extra_kwargs = {
            'price': {'read_only': True},
            'unit_price': {'read_only': True},
        }
        
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']
        
class UserViewSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    class Meta:
        model = User        
        fields = ['id', 'username', 'email', 'password']
        
    def __init__(self, *args, **kwargs):
        super(UserViewSerializer, self).__init__(*args, **kwargs)
        # Check the GET request method and adjust fields accordingly
        request = self.context.get("request")
        if request:
            if request.method == "GET":
                self.fields.pop("password", None)
                
     
class OrderItemSerializer(serializers.ModelSerializer):
    menuitem_id = serializers.PrimaryKeyRelatedField(queryset=Cart.objects.all(), source='menuitem', write_only=True)
    menuitem = MenuItemSerializer(read_only=True)
    class Meta:
        model = OrderItem
        fields = ['order', 'menuitem_id', 'menuitem', 'quantity', 'price']
        extra_kwargs = {
            'quantity': {'read_only': True},
            'price': {'read_only': True},
        }
        
        
class OrderSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    orderitem = OrderItemSerializer(many=True, read_only=True, source='order')
    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew', 'status', 'total', 'date', 'orderitem']