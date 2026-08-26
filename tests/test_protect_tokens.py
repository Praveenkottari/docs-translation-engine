from __future__ import annotations

import re

import pytest

from odt.protect.tokens import protect, restore, TokenMap


CASES = [
    # integers
    ("The value is 42 units.", True),
    # negative integer
    ("Change is -7 units.", True),
    # decimal
    ("Measured: 3.1415 mL", True),
    # negative decimal
    ("Temp: -12.5 °C", True),
    # percentage
    ("Yield: 99%" , True),
    ("Loss: 12.5 %", True),
    # units with MPa
    ("Design Pressure: 10 MPa", True),
    ("Temperature: 120 °C", True),
    # ranges
    ("Range 10-20 units", True),
    ("Range 5 – 15", True),
    # URL and email
    ("See https://example.com/page?x=1", True),
    ("Contact: user@example.co.uk for details", True),
    # file paths
    ("Path: C:\\Program Files\\App\\bin.exe", True),
    ("Path: /usr/local/bin/tool", True),
    # engineering tags and model numbers
    ("Tag: PV-1024 is used", True),
    ("Spec: SA-516 Gr.70 material", True),
    ("Model: ABC-1234-X2", True),
    # chemical formulas
    ("Sample: H2O and C6H12O6 present", True),
    ("Compound: NaCl", False),  # NaCl has no digit; shouldn't match chemical regex
    # times and dates
    ("Event at 14:30:00 on 2021-05-10", True),
    ("Date 10/12/2020 noted", True),
    ("Date 10.12.2020 noted", True),
    # percentages and ppm
    ("Concentration 50 ppm", True),
    ("Accuracy 99.9% reported", True),
    # decimals with commas
    ("Population: 1,234.56", True),
    # emails with plus
    ("Send to first.last+tag@example.com", True),
    # URLs with www
    ("Visit http://www.example.org/test", True),
    # Windows UNC path
    ("\\\\server\\share\\file.txt", True),
    # model/part number with space and dot
    ("Part SA-516 Gr.70 is specified", True),
    # percentage with space
    ("Discount 15 % available", True),
    # value with unit without space
    ("Pressure 10MPa recorded", True),
    # engineering tag lowercase should not match
    ("tag pv-1024 lowercase", False),
    # decimal starting with dot
    ("Value .75 is less than 1", True),
    # numbers inside parentheses
    ("(123) is a number", True),
    # chemical with parentheses C6H5(OH)
    ("Phenol C6H5(OH)", True),
    # path with dotfile
    ("~/.config/app/config.yaml", True),
    # URL with query and fragment
    ("https://example.com/a/b?c=1#frag", True),
    # file path with spaces (quoted)
    ("\"/home/user/My Documents/test.txt\"", True),
    # range with decimals
    ("Tolerance 0.5-1.5 units", True),
    # negative range
    ("Range -5--1 observed", True),
    # engineering tag with many letters
    ("TAG: ABCDE-99999 is present", True),
    # model number with mixed case
    ("Model pv-1024-X not standard", False),
    # chemical with lowercase element (should not match)
    ("molecule: abcdef", False),
    # percent with decimals and comma
    ("Completion 99,95%", True),
]


@pytest.mark.parametrize("text,expect_token", CASES)
def test_protect_restore_roundtrip(text: str, expect_token: bool):
    protected, tmap = protect(text)
    # Protected text should differ if we expect tokens
    if expect_token:
        assert protected != text
        # token format present
        assert re.search(r"__ODT_TOKEN_\d{4}__", protected)
    else:
        # ensure restore works even if no tokens
        assert protected == text or re.search(r"__ODT_TOKEN_\d{4}__", protected) is None

    restored = restore(protected, tmap)
    assert restored == text


def test_tokenmap_no_collision_and_reversible():
    s = "Value 10 MPa and URL https://a.test and Tag PV-1024"
    protected, tmap = protect(s)
    # ensure distinct tokens
    tokens = list(tmap.mapping.keys())
    assert len(tokens) == len(set(tokens))
    # ensure restore recovers original
    assert restore(protected, tmap) == s


def test_many_tokens_and_order():
    s = "A 10 MPa B 20% C PV-100 D /usr/bin/python E user@example.com F C6H12O6"
    protected, tmap = protect(s)
    restored = restore(protected, tmap)
    assert restored == s
