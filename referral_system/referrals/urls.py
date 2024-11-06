from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ReferralCodeViewSet
from django.urls import path, include


from drf_yasg.views import get_schema_view
from drf_yasg import openapi


#from rest_framework_simplejwt.views import TokenObtainPairView
from .views import MyTokenObtainPairView, GenerateReferralCodeView, GetReferralCodeView, RegisterWithReferralCodeView, GetReferralInfoView, GetRefereesInfoView



schema_view = get_schema_view(
    openapi.Info(
        title="referral_system_api",
        default_version='v1',
        description="API description",
    ),
    public=True,
)




router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')  #  регистрация пользователей
router.register(r'referral-codes', ReferralCodeViewSet, basename='referral-codes') #создание/удаление реф кода

urlpatterns = [
    path('', include(router.urls)),
    path('token/', MyTokenObtainPairView.as_view(), name='token_obtain_pair'),  # получение jwt токена
    path('generate-referral-code/', GenerateReferralCodeView.as_view(), name='generate-referral-code'), # создание генерируемого реф кода, у того у кого еще нет реф кода
    path('get-referral-code/', GetReferralCodeView.as_view(), name='get-referral-code'), #получение существующего реф токена по почте
    path('register-with-referral-code/', RegisterWithReferralCodeView.as_view(), name='register-with-referral-code'), #регистрация по реф коду реферера
    path('referral-info/', GetReferralInfoView.as_view(), name='get-referral-info'), #получение инфы о рефераллах по jwt реферера
    path('referees-info/', GetRefereesInfoView.as_view(), name='get-referees-info'),#получение инфы о рефераллах по id реферера
    path('swagger<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),



]

