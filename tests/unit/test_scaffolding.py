"""Confirms the package layout, editable install, and pytest wiring all work end-to-end."""

import urlshortener
import urlshortener.adapters
import urlshortener.api
import urlshortener.application
import urlshortener.domain


def test_urlshortener_package_is_importable():
    assert urlshortener is not None


def test_all_layers_are_importable():
    assert urlshortener.domain is not None
    assert urlshortener.application is not None
    assert urlshortener.adapters is not None
    assert urlshortener.api is not None
