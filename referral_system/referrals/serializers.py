from rest_framework import serializers
from django.contrib.auth.models import User
from .models import ReferralCode, Referral



class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user



class ReferralCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralCode
        fields = ['id', 'code', 'code_expiration_date', 'active']
        read_only_fields = ['id']

    def validate(self, data):
        if self.instance:
            existing_code = ReferralCode.objects.filter(code=data['code'], user=self.context['request'].user).exclude(
                id=self.instance.id).first()
        else:
            existing_code = ReferralCode.objects.filter(code=data['code'], user=self.context['request'].user).first()

        if existing_code:
            raise serializers.ValidationError('Код уже существует для этого пользователя')
        return data



class ReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = Referral
        fields = ['id', 'user', 'referred_by', 'total_referrals', 'total_earnings']
        read_only_fields = ['id', 'created_at', 'updated_at']
