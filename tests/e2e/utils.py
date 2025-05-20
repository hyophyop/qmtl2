"""
Utility functions for Gateway integration tests.

This module provides helper functions for common testing tasks.
"""
import os
import json
import time
from typing import Any, Dict, List, Optional, Union, Type, TypeVar

import grpc
import pytest
import requests
from google.protobuf import json_format
from google.protobuf.message import Message

# Type variable for protobuf messages
T = TypeVar('T', bound=Message)

def assert_proto_equals(actual: Message, expected: Message) -> None:
    """
    Assert that two protobuf messages are equal, providing a detailed diff on failure.
    
    Args:
        actual: The actual protobuf message
        expected: The expected protobuf message
    """
    assert actual == expected, f"\nExpected: {expected}\nActual:   {actual}"

def load_proto_from_json(file_path: str, message_class: Type[T]) -> T:
    """
    Load a protobuf message from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        message_class: The protobuf message class to deserialize into
        
    Returns:
        An instance of the specified protobuf message class
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        json_dict = json.load(f)
    
    message = message_class()
    return json_format.ParseDict(json_dict, message)


def save_proto_to_json(message: Message, file_path: str) -> None:
    """
    Save a protobuf message to a JSON file.
    
    Args:
        message: The protobuf message to save
        file_path: Path to save the JSON file
    """
    json_dict = json_format.MessageToDict(
        message,
        preserving_proto_field_name=True,
        including_default_value_fields=True
    )
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(json_dict, f, indent=2, ensure_ascii=False)


def assert_http_ok(response: requests.Response) -> None:
    """
    Assert that an HTTP response has a 2xx status code.
    
    Args:
        response: The HTTP response to check
    """
    assert 200 <= response.status_code < 300, \
        f"Request failed with status {response.status_code}: {response.text}"


def assert_grpc_ok(call: grpc.Call) -> None:
    """
    Assert that a gRPC call was successful.
    
    Args:
        call: The gRPC call to check
    """
    assert call.code() == grpc.StatusCode.OK, \
        f"gRPC call failed with status {call.code()}: {call.details()}"


def retry_until_success(
    func,
    max_attempts: int = 5,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Retry a function until it succeeds or max attempts are reached.
    
    Args:
        func: The function to retry
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts in seconds
        backoff: Multiplier for delay between attempts
        exceptions: Tuple of exceptions to catch and retry on
        
    Returns:
        The result of the function call if successful
        
    Raises:
        Exception: If max attempts are reached without success
    """
    last_exception = None
    current_delay = delay
    
    for attempt in range(max_attempts):
        try:
            return func()
        except exceptions as e:
            last_exception = e
            if attempt < max_attempts - 1:  # Don't sleep on the last attempt
                time.sleep(current_delay)
                current_delay *= backoff
    
    # If we get here, all attempts failed
    raise last_exception if last_exception else Exception("Failed after retries")


def assert_dict_contains(actual: dict, expected: dict) -> None:
    """
    Assert that the actual dictionary contains all the key-value pairs from the expected dictionary.
    
    Args:
        actual: The dictionary to check
        expected: The dictionary of expected key-value pairs
    """
    for key, expected_value in expected.items():
        assert key in actual, f"Key '{key}' not found in actual dictionary"
        assert actual[key] == expected_value, \
            f"Value mismatch for key '{key}': expected {expected_value!r}, got {actual[key]!r}"


def assert_proto_contains(actual: Message, expected: Message) -> None:
    """
    Assert that the actual protobuf message contains all the fields from the expected message.
    
    Args:
        actual: The actual protobuf message
        expected: The expected protobuf message with fields to check
    """
    actual_dict = json_format.MessageToDict(actual, including_default_value_fields=True)
    expected_dict = json_format.MessageToDict(expected, including_default_value_fields=True)
    
    # Check that all fields in expected exist in actual with the same values
    for key, expected_value in expected_dict.items():
        assert key in actual_dict, f"Field '{key}' not found in actual message"
        assert actual_dict[key] == expected_value, \
            f"Value mismatch for field '{key}': expected {expected_value!r}, got {actual_dict[key]!r}"


def generate_test_data(
    count: int = 10,
    prefix: str = "test"
) -> List[Dict[str, Any]]:
    """
    Generate a list of test data dictionaries.
    
    Args:
        count: Number of test items to generate
        prefix: Prefix for generated values
        
    Returns:
        List of test data dictionaries
    """
    return [
        {
            "id": f"{prefix}_{i}",
            "name": f"{prefix.capitalize()} Item {i}",
            "value": i,
            "active": i % 2 == 0,
            "tags": [f"tag_{j}" for j in range(i % 3 + 1)],
            "metadata": {"key1": f"value_{i}_1", "key2": f"value_{i}_2"}
        }
        for i in range(1, count + 1)
    ]


def mock_grpc_service(service_name: str, methods: List[str]):
    """
    Create a mock gRPC service with the specified methods.
    
    Args:
        service_name: Name of the gRPC service
        methods: List of method names to mock
        
    Returns:
        A mock gRPC service
    """
    # Create a mock class for the service
    mock_service = type(
        f"Mock{service_name}",
        (object,),
        {method: MagicMock() for method in methods}
    )
    
    return mock_service()


def setup_mock_responses(mock_client, responses: Dict[str, Any]) -> None:
    """
    Set up mock responses for a mock client.
    
    Args:
        mock_client: The mock client to configure
        responses: Dictionary mapping method names to return values or callable
    """
    for method_name, response in responses.items():
        method = getattr(mock_client, method_name, None)
        if method is not None:
            if callable(response):
                method.side_effect = response
            else:
                method.return_value = response
