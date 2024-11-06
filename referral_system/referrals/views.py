from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser, IsAuthenticatedOrReadOnly
from .serializers import UserSerializer, ReferralSerializer
from django.contrib.auth.models import User
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import ReferralCode, Referral
from .serializers import ReferralCodeSerializer

from rest_framework.views import APIView
# from datetime import timezone
# from django.utils import timezone
from django.utils import timezone

import random
import string
from zoneinfo import ZoneInfo
from datetime import datetime
from django.core.mail import send_mail
import logging
logger = logging.getLogger(__name__)



class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]  #  разрешил доступ без аутентификации для регистрации



class ReferralCodeViewSet(viewsets.ModelViewSet):
    queryset = ReferralCode.objects.all()
    serializer_class = ReferralCodeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ReferralCode.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        instance.delete()



class MyTokenObtainPairView(TokenObtainPairView):
    # что-то если нужно
    pass



class GenerateReferralCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # получаю текущего пользователяя
        user = request.user

        # генерируем уникальный код
        code = generate_unique_code(user)

        # создаем новый реферальный код
        new_code = ReferralCode.objects.create(
            user=user,
            code=code,
            code_expiration_date=datetime.now(tz=ZoneInfo("UTC")) + timezone.timedelta(days=365),  # код действителен год
            active=True
        )

        # сериализую  новый код
        serializer = ReferralCodeSerializer(new_code)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


def generate_unique_code(user):
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=30))

    while ReferralCode.objects.filter(code=code, user=user).exists():
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=30))

    return code



class GetReferralCodeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        referral_code = ReferralCode.objects.filter(user=user).first()

        if referral_code and referral_code.active:
            subject = 'Ваш реферальный код'
            message = f'Ваш реферальный код: {referral_code.code}'
            email_from = 'a.plehanov2002@mail.ru'
            email_to = user.email

            send_mail(
                subject,
                message,
                email_from,
                [email_to],
                fail_silently=False,
            )

            return Response({'message': 'Реферальный код отправлен на вашу почту'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'У вас нет активного реферального кода'}, status=status.HTTP_404_NOT_FOUND)



class RegisterWithReferralCodeView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        referral_code = request.data.get('referral_code')
        if not referral_code:
            return Response({'error': 'Не указан реферальный код'}, status=status.HTTP_400_BAD_REQUEST)

        existing_referral = ReferralCode.objects.filter(code=referral_code).first()
        if not existing_referral:
            return Response({'error': 'Неверный реферальный код'}, status=status.HTTP_400_BAD_REQUEST)

        if existing_referral.user == request.user:
            return Response({'error': 'Вы уже зарегистрированы с этим реферальным кодом'},
                            status=status.HTTP_400_BAD_REQUEST)

        # Создаем нового пользователя
        username = f"{existing_referral.user.username}_referal_{random.randint(1000, 9999)}"
        new_user = User.objects.create(username=username, email=request.data.get('email'))

        Referral.objects.create(
            user=new_user,
            referred_by=existing_referral.user
        )

        # генерируем новый реферальный код
        new_referral_code = generate_unique_code(new_user)

        # создаем новый реферальный код
        ReferralCode.objects.create(
            user=new_user,
            code=new_referral_code,
            active=True
        )

        # отправляем новый реферальный код пользователю
        subject = 'Ваш новый реферальный код'
        message = f'Ваш новый реферальный код: {new_referral_code}'
        email_from = 'a.plehanov2002@mail.ru'
        email_to = new_user.email

        send_mail(
            subject,
            message,
            email_from,
            [email_to],
            fail_silently=False,
        )

        return Response({'message': 'Вы успешно зарегистрированы с использованием реферального кода'},
                        status=status.HTTP_201_CREATED)



class GetReferralInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logger.info(f"Получение реферальной информации для пользователя: {request.user}")
        user = request.user
        referral = Referral.objects.filter(referred_by=user).all()

        if referral:
            serializer = ReferralSerializer(referral, many=True)
            return Response(serializer.data)
        else:
            logger.warning(f"Для пользователя не найдено ни одной ссылки: {user}")
            return Response({'error': 'Информация о рефералах отсутствует'}, status=status.HTTP_404_NOT_FOUND)



class GetRefereesInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        referrer_id = request.GET.get('referrer_id')
        if not referrer_id:
            return Response({'error': 'Требуется идентификатор реферера'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            referrer = User.objects.get(id=referrer_id)
            referrals = Referral.objects.filter(referred_by=referrer)

            if referrals:
                serializer = ReferralSerializer(referrals, many=True)
                return Response(serializer.data)
            else:
                return Response({'error': 'Для этого реферера не найдено ни одного реферала'}, status=status.HTTP_404_NOT_FOUND)
        except User.DoesNotExist:
            return Response({'error': 'Реферер не найден'}, status=status.HTTP_404_NOT_FOUND)
