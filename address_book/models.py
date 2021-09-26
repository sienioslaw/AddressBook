from django.contrib.auth.models import User
from django.db import models


class Address(models.Model):
    user = models.ForeignKey(User, related_name='addresses', null=True, on_delete=models.CASCADE)
    street = models.CharField(max_length=300)
    city = models.CharField(max_length=300)
    postcode = models.CharField(max_length=300)
    country = models.CharField(max_length=300)

    class Meta:
        unique_together = ["user", "street", "city", "country"]

    def __str__(self):
        return '%s, %s, %s, %s' % (self.street, self.city, self.postcode, self.country)