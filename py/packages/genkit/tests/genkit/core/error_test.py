# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for the error module."""

import pytest
from genkit.core.error import (
    GenkitError,
    HttpErrorWireFormat,
    UnstableApiError,
    UserFacingError,
    assert_unstable,
    get_callable_json,
    get_error_message,
    get_error_stack,
    get_http_status,
)
from genkit.core.registry import Registry


def test_assert_unstable() -> None:
    """Test assert_unstable works."""

    registry: Registry = Registry()
    registry.api_stability = 'stable'

    with pytest.raises(UnstableApiError):
        assert_unstable(registry, level='beta')

    with pytest.raises(UnstableApiError):
        assert_unstable(registry)  # Default is beta.


# New tests start here
def test_genkit_error() -> None:
    """Test that creating a GenkitError works."""
    error = GenkitError(
        status='INVALID_ARGUMENT',
        message='Test message',
        detail='Test detail',
        source='test_source',
    )
    assert error.original_message == 'Test message'
    assert error.code == 400
    assert error.status == 'INVALID_ARGUMENT'
    assert error.detail == 'Test detail'
    assert error.source == 'test_source'
    assert str(error) == 'test_source: INVALID_ARGUMENT: Test message'

    # Test without source
    error_no_source = GenkitError(status='INTERNAL', message='Test message 2')
    assert str(error_no_source) == 'INTERNAL: Test message 2'


def test_genkit_error_to_json() -> None:
    """Test that GenkitError can be serialized to JSON."""
    error = GenkitError(
        status='NOT_FOUND', message='Resource not found', detail={'id': 123}
    )
    serializable = error.to_serializable()
    assert isinstance(serializable, HttpErrorWireFormat)
    assert serializable.status == 'NOT_FOUND'
    assert serializable.message == 'Resource not found'
    assert serializable.details == {'id': 123}


def test_unstable_api_error() -> None:
    """Test that creating an UnstableApiError works."""
    error = UnstableApiError(level='alpha', message='Test feature')
    assert error.status == 'FAILED_PRECONDITION'
    assert 'Test feature' in error.original_message
    assert "This API requires 'alpha' stability level" in error.original_message

    error_no_message = UnstableApiError()
    assert (
        "This API requires 'beta' stability level"
        in error_no_message.original_message
    )


def test_user_facing_error() -> None:
    """Test creating a UserFacingError."""
    error = UserFacingError(
        status='UNAUTHENTICATED',
        message='Please log in',
        details='Session expired',
    )
    assert error.status == 'UNAUTHENTICATED'
    assert error.original_message == 'Please log in'
    assert error.detail == 'Session expired'


def test_get_http_status() -> None:
    """Test that get_http_status returns the correct HTTP status code."""
    genkit_error = GenkitError(status='PERMISSION_DENIED', message='No access')
    assert get_http_status(genkit_error) == 403

    non_genkit_error = ValueError('Some other error')
    assert get_http_status(non_genkit_error) == 500


def test_get_callable_json() -> None:
    """Test that get_callable_json returns the correct JSON data."""
    genkit_error = GenkitError(status='DATA_LOSS', message='Oops')
    json_data = get_callable_json(genkit_error)
    assert isinstance(json_data, HttpErrorWireFormat)
    assert json_data.status == 'DATA_LOSS'
    assert json_data.message == 'Oops'

    non_genkit_error = TypeError('Type error')
    json_data = get_callable_json(non_genkit_error)
    assert isinstance(json_data, HttpErrorWireFormat)
    assert json_data.status == 'INTERNAL'
    assert json_data.message == 'Internal Error'


def test_get_error_message() -> None:
    """Test that get_error_message returns the correct error message."""
    error_message = get_error_message(ValueError('Test Value Error'))
    assert error_message == 'Test Value Error'

    error_message = get_error_message('Test String Error')
    assert error_message == 'Test String Error'


def test_get_error_stack() -> None:
    """Test that get_error_stack returns the correct error stack."""
    try:
        raise ValueError('Example Error')
    except ValueError as e:
        tb = get_error_stack(e)
        assert tb is not None
        assert 'Example Error' in tb
