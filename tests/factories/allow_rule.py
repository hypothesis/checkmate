import factory
from checkmatelib.url import hash_for_rule
from factory import Faker
from factory.alchemy import SQLAlchemyModelFactory

from checkmate import models


class AllowRule(SQLAlchemyModelFactory):
    class Meta:
        model = models.AllowRule
        exclude = ("url",)

    url = Faker("url")

    # The real attributes
    rule = factory.LazyAttribute(lambda o: hash_for_rule(o.url)[0])
    hash = factory.LazyAttribute(lambda o: hash_for_rule(o.url)[1])
