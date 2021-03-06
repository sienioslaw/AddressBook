from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from .models import Address
from faker import Faker
import random


class AddressAPITestCase(TestCase):

    def setUp(self):
        self.username = 'testuser'
        self.username_alt = 'testuser1'
        self.password = '12345'
        self.password_alt = '54321'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        self.user_alt = User.objects.create_user(username=self.username_alt, password=self.password_alt)
        self.client = APIClient()

    def authenticate_client(self, username, password):
        data = {'username': username, 'password': password}
        response = self.client.post("/api/auth/login", data=data, format="json")
        token = response.data['auth_token']
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

    def create_sample_addresses(self, user, count):
        fake = Faker()
        for _ in range(0, count):
            fake.seed_instance(random.randint(0, 99999))
            data = {
                "user": user,
                "street": fake.street_address(),
                "city": fake.city(),
                "postcode": fake.postcode(),
                "country": fake.country()
            }
            Address.objects.create(**data)

    # User is able to authenticate with a username and a password
    def testRetrievingToken(self):
        # make sure that user have no token assigned
        is_tokened = Token.objects.filter(user=self.user).first()
        self.assertTrue(is_tokened is None)

        data = {'username': self.username, 'password': self.password}
        response = self.client.post("/api/auth/login", data=data, format="json")
        self.assertEqual(response.status_code, 200)
        token = response.data['auth_token']
        self.assertEqual(self.user.auth_token.key, token)

    # User can log out
    def testLogoutAPIEndpoint(self):
        data = {'username': self.username, 'password': self.password}
        response = self.client.post("/api/auth/login", data=data, format="json")
        token = response.data['auth_token']

        # verify that token exist
        self.assertTrue(self.user.auth_token)

        # logout require providing token
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)
        response = self.client.post("/api/auth/logout", data=data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data,{'success': 'Sucessfully logged out'})
        self.assertTrue(Token.objects.filter(user=self.user).first() is None)

    # User is able to create a new address
    # User will not be able to add a duplicated address to their account
    def testUserAbilityToCreateNewAdressEndpoint(self):
        self.authenticate_client(self.username, self.password)

        data = {
            "street": '133-137 Fetter Ln',
            "city": 'London',
            "postcode": 'EC4A 2BB',
            "country": 'United Kingdom'
        }
        # user should not have addresses before adding through API
        self.assertEqual(self.user.addresses.count(), 0)

        response = self.client.post("/api/addresses", data=data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.user.addresses.count(), 1)

        # now lets call endpoint with the same params to make sure it that we wont end up with duplicate
        response = self.client.post("/api/addresses", data=data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'error': 'User already have this address'})
        
        self.assertEqual(self.user.addresses.count(), 1)
        self.assertEqual(Address.objects.all().count(), 1)

    # User is able to retrieve all their postal addresses
    def testUserAbilityToRetrieveAdressesEndpoint(self):
        self.create_sample_addresses(self.user, 3)
        self.create_sample_addresses(self.user_alt, 7)
        self.authenticate_client(self.username, self.password)

        response = self.client.get("/api/addresses", format="json")
        self.assertEqual(response.status_code, 200)
        user_address_count = self.user.addresses.count() # 3
        self.assertEqual(user_address_count, len(response.data['results']))

        # reset ApiClient
        self.client = APIClient()
        self.authenticate_client(self.username_alt, self.password_alt)
        response = self.client.get("/api/addresses", format="json")
        self.assertEqual(response.status_code, 200)
        user_address_count = self.user_alt.addresses.count() # 7
        self.assertEqual(user_address_count, len(response.data['results']))

    # User is able to filter retrieved addresses using request parameters
    def testUserAbilityToRetrieveFilteredAddressesEndpoint(self):
        # create non-random sample data for sake of testing    	
        data = [{
            "user": self.user,
            "street": 'Rope street',
            "city": 'London',
            "postcode": 'SE16 7FJ',
            "country": 'United Kingdom'
        }, {
            "user": self.user,
            "street": '133-137 Fetter Ln',
            "city": 'London',
            "postcode": 'EC4A 2BB',
            "country": 'United Kingdom'
        }, {
            "user": self.user,
            "street": 'Dluga',
            "city": 'Gdansk',
            "postcode": '111-93',
            "country": 'Poland'
        }]
        for entry in data:
        	Address.objects.create(**entry)

        self.authenticate_client(self.username, self.password)

        # example filter by city
        response = self.client.get("/api/addresses?city=Gdansk", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, response.data['count'])
        response = self.client.get("/api/addresses?city=London", format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(2, response.data['count'])

    # User is able to update existing addresses
    def testUserAbilityToUpdateAddressEndpoint(self):
        self.authenticate_client(self.username, self.password)
        data = {
            "user": self.user,
            "street": 'Rope street',
            "city": 'London',
            "postcode": 'SE16 7FJ',
            "country": 'United Kingdom'
        }
        address = Address.objects.create(**data)

        new_data = data.copy()
        del new_data['user']
        new_data['city'] = 'Manchester'

        url = "/api/addresses/%s" % address.id
        response = self.client.put(url, data=new_data, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.user.addresses.count(), 1)
        self.assertEqual(self.user.addresses.all()[0].city, new_data['city'])

    # User is able to delete one
    def testUserAbilityToDeleteAddressEndpoint(self):
        self.authenticate_client(self.username, self.password)
        data = {
            "user": self.user,
            "street": 'Rope street',
            "city": 'London',
            "postcode": 'SE16 7FJ',
            "country": 'United Kingdom'
        }
        address = Address.objects.create(**data)

        # make sure that user got address stored
        self.assertEqual(self.user.addresses.count(), 1)

        url = "/api/addresses/%s" % address.id
        response = self.client.delete(url, format="json")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.user.addresses.count(), 0)

    # User is able to delete multiple addresses
    def testUserAbilityToDeleteMultipleAddressEndpoint(self):
        # create non-random sample data for sake of testing    	
        data = [{
            "user": self.user,
            "street": 'Rope street',
            "city": 'London',
            "postcode": 'SE16 7FJ',
            "country": 'United Kingdom'
        }, {
            "user": self.user,
            "street": '133-137 Fetter Ln',
            "city": 'London',
            "postcode": 'EC4A 2BB',
            "country": 'United Kingdom'
        }, {
            "user": self.user,
            "street": 'Dluga',
            "city": 'Gdansk',
            "postcode": '111-93',
            "country": 'Poland'
        }]
        ids = []
        for entry in data:
        	entry = Address.objects.create(**entry)
        	ids.append(entry.id)

        self.authenticate_client(self.username, self.password)

        self.assertEqual(3, self.user.addresses.count())

        # for sake of test we will send only 2 ids
        ids.pop()
        url = "/api/addresses/delete_multiple?ids=%s" % ','.join([str(x) for x in ids])
        response = self.client.delete(url, format="json")
        self.assertEqual(1, self.user.addresses.count())
