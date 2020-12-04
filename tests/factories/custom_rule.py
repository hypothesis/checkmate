import factory
from factory import Faker
from factory.alchemy import SQLAlchemyModelFactory

from checkmate.checker.url.reason import Reason
from checkmate.models.data import custom_rule
from checkmate.url import hash_for_rule

REASONS = list(Reason)


class CustomRule(SQLAlchemyModelFactory):
    class Meta:
        model = custom_rule.CustomRule
        exclude = ("url", "reasons")

    url = Faker("url")
    reasons = Faker("random_elements", elements=REASONS, unique=True)

    # The real attributes
    rule = factory.LazyAttribute(lambda o: hash_for_rule(o.url)[0])
    hash = factory.LazyAttribute(lambda o: hash_for_rule(o.url)[1])
    tags = factory.LazyAttribute(lambda o: [reason.value for reason in o.reasons])
