from django.urls import path
from .views import ProductionPlanView

urlpatterns = [
    path('productionplan', ProductionPlanView.as_view(), name='production-plan'),
]