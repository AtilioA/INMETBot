import sys
sys.path.append('..')

import pytest
from bot_utils import determine_severity_emoji

with open("test_severity_emoji.txt", "r+", encoding="utf8") as f:
    input_severity_emoji = [eval(tupla) for tupla in f.readlines()]
print(input_severity_emoji)


@pytest.mark.parametrize("test_input, expected", input_severity_emoji)
def test_determine_severity_emoji(test_input, expected):
    assert determine_severity_emoji(test_input) == expected
