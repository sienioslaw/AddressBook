from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from address_book.models import Address
from faker import Faker
import random


class Command(BaseCommand):

	def handle(self, *args, **options):
		breakpoint()
		fake = Faker()
		for user in User.objects.all():
			for _ in range(0, 100):
				fake.seed_instance(random.randint(0, 99999))
				try:
					data = {
						"user": user,
						"street": fake.street_address(),
						"city": fake.city(),
						"postcode": fake.postcode(),
						"country": fake.country()
					}
					Address.objects.create(**data)
				except Exception:
					# there is a very slim chance we would trigger constrain, but still...
					pass
