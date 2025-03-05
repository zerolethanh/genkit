# Copyright 2025 Google LLC
# SPDX-License-Identifier: Apache-2.0

import pytest
from genkit.core.extract import extract_items, extract_json, parse_partial_json

# TODO: consider extracting these tests into shared yaml spec. They are already
# duplicated in js/ai/tests/extract_test.ts

test_cases_extract_items = [
    (
        'handles simple array in chunks',
        [
            {'chunk': '[', 'want': []},
            {'chunk': '{"a": 1},', 'want': [{'a': 1}]},
            {'chunk': '{"b": 2}', 'want': [{'b': 2}]},
            {'chunk': ']', 'want': []},
        ],
    ),
    (
        'handles nested objects',
        [
            {'chunk': '[{"outer": {', 'want': []},
            {
                'chunk': '"inner": "value"}},',
                'want': [{'outer': {'inner': 'value'}}],
            },
            {'chunk': '{"next": true}]', 'want': [{'next': True}]},
        ],
    ),
    (
        'handles escaped characters',
        [
            {'chunk': '[{"text": "line1\\n', 'want': []},
            {
                'chunk': 'line2"},',
                'want': [{'text': 'line1\nline2'}],
            },
            {
                'chunk': '{"text": "tab\\there"}]',
                'want': [{'text': 'tab\there'}],
            },
        ],
    ),
    (
        'ignores content before first array',
        [
            {'chunk': 'Here is an array:\n```json\n\n[', 'want': []},
            {'chunk': '{"a": 1},', 'want': [{'a': 1}]},
            {
                'chunk': '{"b": 2}]\n```\nDid you like my array?',
                'want': [{'b': 2}],
            },
        ],
    ),
    (
        'handles whitespace',
        [
            {'chunk': '[\n  ', 'want': []},
            {'chunk': '{"a": 1},\n  ', 'want': [{'a': 1}]},
            {'chunk': '{"b": 2}\n]', 'want': [{'b': 2}]},
        ],
    ),
]


@pytest.mark.parametrize(
    'name, steps',
    test_cases_extract_items,
    ids=[tc[0] for tc in test_cases_extract_items],
)
def test_extract_items(name, steps):
    text = ''
    cursor = 0
    for step in steps:
        text += step['chunk']
        result = extract_items(text, cursor)
        assert result.items == step['want']
        cursor = result.cursor


test_cases_extract_json = [
    (
        'extracts simple object',
        {'text': 'prefix{"a":1}suffix'},
        {'expected': {'a': 1}},
    ),
    (
        'extracts simple array',
        {'text': 'prefix[1,2,3]suffix'},
        {'expected': [1, 2, 3]},
    ),
    (
        'handles nested structures',
        {'text': 'text{"a":{"b":[1,2]}}more'},
        {'expected': {'a': {'b': [1, 2]}}},
    ),
    (
        'handles strings with braces',
        {'text': '{"text": "not {a} json"}'},
        {'expected': {'text': 'not {a} json'}},
    ),
    (
        'returns null for invalid JSON without throw',
        {'text': 'not json at all'},
        {'expected': None},
    ),
    (
        'throws for invalid JSON with throw flag',
        {'text': 'not json at all', 'throwOnBadJson': True},
        {'throws': True},
    ),
]


@pytest.mark.parametrize(
    'name, input_data, expected_data',
    test_cases_extract_json,
    ids=[tc[0] for tc in test_cases_extract_json],
)
def test_extract_json(name, input_data, expected_data):
    if expected_data.get('throws'):
        with pytest.raises(Exception):
            extract_json(input_data['text'], throw_on_bad_json=True)
    else:
        result = extract_json(
            input_data['text'],
            throw_on_bad_json=input_data.get('throwOnBadJson', False),
        )
        assert result == expected_data['expected']


test_cases_parse_partial_json = [
    (
        'parses complete object',
        '{"a":1,"b":2}',
        {'expected': {'a': 1, 'b': 2}},
    ),
    (
        'parses partial object',
        '{"a":1,"b":',
        {'expected': {'a': 1}},
    ),
    (
        'parses partial array',
        '[1,2,3,',
        {'expected': [1, 2, 3]},
    ),
    # NOTE: this testcase diverges from the one in js/ai/tests/extract_test.ts
    # Specifically, python partial json parser lib doesn't like malformed json.
    # JS one handles input: '{"a":{"b":1,"c":]}}',
    (
        'parses nested partial structures',
        '{"a":{"b":1,"c":[',
        {'expected': {'a': {'b': 1, 'c': []}}},
    ),
]


@pytest.mark.parametrize(
    'name, input_str, expected_data',
    test_cases_parse_partial_json,
    ids=[tc[0] for tc in test_cases_parse_partial_json],
)
def test_parse_partial_json(name, input_str, expected_data):
    result = parse_partial_json(input_str)
    assert result == expected_data['expected']
