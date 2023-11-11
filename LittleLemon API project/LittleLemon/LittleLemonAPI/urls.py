from django.urls import path
from . import views
from rest_framework.authtoken.views import obtain_auth_token

urlpatterns = [
    # path('api-token-auth/', obtain_auth_token),
    # path('manager-view/', views.manager_view),
    # path('throttle-check/', views.throttle_check),
    # path('throttle-check-auth/', views.throttle_check_auth),
    path('users/', views.UserView.as_view()),
    path('menu-items/', views.MenuItemsView.as_view()),
    path('menu-items/<int:pk>', views.SingleMenuItemView.as_view()),
    path('cart/menu-items/', views.CartListCreateDestroyView.as_view()),
    path('users/users/me/', views.CurrentUserView.as_view()),
    path('orders/', views.OrderView.as_view()),
    path('orders/<int:pk>', views.SingleOrderView.as_view()),
    path('groups/manager/users', views.ManagerListCreateView.as_view()),
    path('groups/manager/users/<int:id>', views.ManagerDeleteView.as_view()),
    path('groups/delivery-crew/users', views.DeliveryListCreateView.as_view()),
    path('groups/delivery-crew/users/<int:id>', views.DeliveryDeleteView.as_view()),
]