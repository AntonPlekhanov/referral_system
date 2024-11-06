from datetime import timezone

from django.db import models
from django.contrib.auth.models import User
from django.db.models import OneToOneField



class ReferralCode(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE)
    code = models.CharField(max_length = 30, unique = True)
    code_expiration_date = models.DateTimeField(null=True, blank=True)
    active = models.BooleanField(default=True) #добавил

    def create(self, validated_data):
        self.user = User.objects.get(id=validated_data['user_id'])
        self.code = validated_data['code']
        self.code_expiration_date = validated_data['expiration_date']
        self.save()

    def delete(self):
        self.active = False
        self.save()

    def __str__(self):
        return self.code

    @property
    def is_active(self):
        return self.active and self.code_is_active()

    def code_is_active(self):
        return self.code_expiration_date > timezone.now()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['code', 'user'], name='unique_referral_code_per_user'),
        ]

    def __str__(self):
        return f"{self.code} - {self.user.username}"



class Referral(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    referred_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='referred_users', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s referral"

    @property
    def total_referrals(self):
        return self.referral_set.count()

    @property
    def total_earnings(self):
        return sum(referral.earning_amount for referral in self.referral_set.all())
