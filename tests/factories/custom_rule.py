import factory
from checkmatelib.url import hash_for_rule
from factory import Faker
from factory.alchemy import SQLAlchemyModelFactory

from checkmate import models

REASONS = list(models.Reason)


class CustomRule(SQLAlchemyModelFactory):
    class Meta:
        model = models.CustomRule
        exclude = ("url", "reasons")

    url = Faker("url")
    reasons = Faker("random_elements", elements=REASONS, unique=True)

    # The real attributes
    rule = factory.LazyAttribute(lambda o: hash_for_rule(o.url)[0])
    hash = factory.LazyAttribute(lambda o: hash_for_rule(o.url)[1])
    tags = factory.LazyAttribute(lambda o: [reason.value for reason in o.reasons])
