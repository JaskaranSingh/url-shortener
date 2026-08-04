import secrets
from unittest.mock import patch

from urlshortener.application.short_code_generator import ALPHABET, CODE_LENGTH, ShortCodeGenerator


def test_generate_returns_correct_length():
    code = ShortCodeGenerator().generate()
    assert len(code) == CODE_LENGTH


def test_generate_only_uses_alphabet_characters():
    code = ShortCodeGenerator().generate()
    assert all(ch in ALPHABET for ch in code)


def test_generate_produces_unique_codes_at_volume():
    codes = {ShortCodeGenerator().generate() for _ in range(10_000)}
    assert len(codes) == 10_000


def test_generate_uses_secrets_choice_not_random():
    """Locks in CSPRNG usage structurally, not just via output appearance."""
    with patch(
        "urlshortener.application.short_code_generator.secrets.choice",
        wraps=secrets.choice,
    ) as mock_choice:
        ShortCodeGenerator().generate()
    assert mock_choice.call_count == CODE_LENGTH
