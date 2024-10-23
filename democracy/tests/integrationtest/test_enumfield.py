import pytest
from enumfields import Enum
from rest_framework.exceptions import ValidationError

from democracy.utils.drf_enum_field import EnumField


class PeculiarEnum(Enum):
    COOL = 1
    HOT = 100
    BLEGBLAGPLEPLOP = "foo"


def test_enum():
    ef = EnumField(enum_type=PeculiarEnum)
    assert ef.to_representation(PeculiarEnum.COOL) == "cool"
    assert ef.to_representation(PeculiarEnum.HOT) == "hot"
    assert ef.to_representation(PeculiarEnum.BLEGBLAGPLEPLOP) == "foo"
    assert ef.to_representation(None) is None
    assert ef.to_internal_value("cool") == PeculiarEnum.COOL
    assert ef.to_internal_value("CooL") == PeculiarEnum.COOL
    assert ef.to_internal_value("HOT") == PeculiarEnum.HOT
    assert ef.to_internal_value(1) == PeculiarEnum.COOL
    assert ef.to_internal_value("100") == PeculiarEnum.HOT
    assert ef.to_internal_value("foo") == PeculiarEnum.BLEGBLAGPLEPLOP
    assert ef.to_internal_value("fOO") == PeculiarEnum.BLEGBLAGPLEPLOP
    assert ef.to_internal_value("BLEGBLAGPLEPLOP") == PeculiarEnum.BLEGBLAGPLEPLOP
    with pytest.raises(ValidationError):
        ef.to_internal_value("jmsdfkgi")
