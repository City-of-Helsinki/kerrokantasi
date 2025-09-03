import pytest
from django.db.models import IntegerChoices, TextChoices
from rest_framework.exceptions import ValidationError

from democracy.utils.drf_enum_field import EnumField


class PeculiarIntegerEnum(IntegerChoices):
    COOL = 1
    HOT = 100


class PeculiarTextEnum(TextChoices):
    BLEGBLAGPLEPLOP = "foo"


def test_integer_enum():
    ef = EnumField(enum_type=PeculiarIntegerEnum)
    assert ef.to_representation(PeculiarIntegerEnum.COOL) == "cool"
    assert ef.to_representation(PeculiarIntegerEnum.HOT) == "hot"
    assert ef.to_representation(None) is None
    assert ef.to_internal_value("cool") == PeculiarIntegerEnum.COOL
    assert ef.to_internal_value("CooL") == PeculiarIntegerEnum.COOL
    assert ef.to_internal_value("HOT") == PeculiarIntegerEnum.HOT
    assert ef.to_internal_value(1) == PeculiarIntegerEnum.COOL
    assert ef.to_internal_value("100") == PeculiarIntegerEnum.HOT
    with pytest.raises(ValidationError):
        ef.to_internal_value("jmsdfkgi")


def test_text_enum():
    ef = EnumField(enum_type=PeculiarTextEnum)

    assert ef.to_representation(PeculiarTextEnum.BLEGBLAGPLEPLOP) == "foo"
    assert ef.to_internal_value("foo") == PeculiarTextEnum.BLEGBLAGPLEPLOP
    assert ef.to_internal_value("fOO") == PeculiarTextEnum.BLEGBLAGPLEPLOP
    assert ef.to_internal_value("BLEGBLAGPLEPLOP") == PeculiarTextEnum.BLEGBLAGPLEPLOP
    with pytest.raises(ValidationError):
        ef.to_internal_value("jmsdfkgi")
