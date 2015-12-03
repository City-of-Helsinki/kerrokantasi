# -*- coding: utf-8 -*-
from democracy.models import Label


def test_label_str():
    assert str(Label(label="label")) == "label"
