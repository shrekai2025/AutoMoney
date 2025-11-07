"""Robust JSON parser for LLM responses"""

import json
import re
from typing import Any, Dict


class JSONParseError(Exception):
    """Custom exception for JSON parsing errors"""
    pass


def extract_json_from_text(text: str) -> str:
    """
    Extract JSON content from text that may contain extra information

    Handles cases like:
    - Text before JSON: "Here's the analysis: {...}"
    - Text after JSON: "{...}\n\nLet me know if you need more info"
    - JSON wrapped in markdown: "```json\n{...}\n```"
    - Multiple JSON objects: takes the first complete one

    Args:
        text: Raw text that contains JSON

    Returns:
        Cleaned JSON string

    Raises:
        JSONParseError: If no valid JSON found
    """
    if not text or not isinstance(text, str):
        raise JSONParseError("Input text is empty or not a string")

    # Remove common markdown code block wrappers
    text = text.strip()

    # Method 1: Try to find JSON in markdown code blocks
    markdown_patterns = [
        r"```json\s*\n(.*?)\n```",  # ```json\n...\n```
        r"```\s*\n(.*?)\n```",       # ```\n...\n```
    ]

    for pattern in markdown_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            text = matches[0].strip()
            break

    # Method 2: Find first { and last } to extract JSON object
    first_brace = text.find('{')
    last_brace = text.rfind('}')

    if first_brace == -1 or last_brace == -1 or first_brace >= last_brace:
        # Try to find JSON array instead
        first_bracket = text.find('[')
        last_bracket = text.rfind(']')

        if first_bracket == -1 or last_bracket == -1 or first_bracket >= last_bracket:
            raise JSONParseError(f"No valid JSON object or array found in text: {text[:100]}...")

        json_str = text[first_bracket:last_bracket + 1]
    else:
        # Extract from first { to last }
        json_str = text[first_brace:last_brace + 1]

    # Clean up the extracted JSON string
    json_str = json_str.strip()

    return json_str


def parse_llm_json(text: str, expected_fields: list = None) -> Dict[str, Any]:
    """
    Parse JSON from LLM response with robust error handling

    Args:
        text: Raw LLM response text
        expected_fields: Optional list of field names that must be present

    Returns:
        Parsed JSON dictionary

    Raises:
        JSONParseError: If JSON cannot be parsed or required fields are missing
    """
    try:
        # Step 1: Extract JSON from text
        json_str = extract_json_from_text(text)

        # Step 2: Parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            # Try to fix common JSON issues
            json_str = fix_common_json_issues(json_str)
            try:
                data = json.loads(json_str)
            except json.JSONDecodeError:
                raise JSONParseError(f"Invalid JSON after cleanup: {str(e)}\nJSON: {json_str[:200]}...")

        # Step 3: Validate expected fields
        if expected_fields:
            missing_fields = [field for field in expected_fields if field not in data]
            if missing_fields:
                raise JSONParseError(f"Missing required fields: {missing_fields}")

        return data

    except JSONParseError:
        raise
    except Exception as e:
        raise JSONParseError(f"Unexpected error parsing JSON: {str(e)}")


def fix_common_json_issues(json_str: str) -> str:
    """
    Fix common JSON formatting issues from LLM responses

    Args:
        json_str: JSON string that may have issues

    Returns:
        Fixed JSON string
    """
    # 1. Remove trailing commas before closing braces/brackets
    json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

    # 2. Fix unescaped newlines in string values
    # This is the most common issue - LLM puts real newlines instead of \n
    # Use a simple character-by-character approach to properly handle string boundaries
    result = []
    in_string = False
    escape_next = False
    i = 0

    while i < len(json_str):
        char = json_str[i]

        if escape_next:
            # This character is escaped, keep it as-is
            result.append(char)
            escape_next = False
        elif char == '\\':
            # Next character will be escaped
            result.append(char)
            escape_next = True
        elif char == '"':
            # Toggle string mode
            in_string = not in_string
            result.append(char)
        elif in_string:
            # Inside a string - escape special characters
            if char == '\n':
                result.append('\\n')
            elif char == '\t':
                result.append('\\t')
            elif char == '\r':
                result.append('\\r')
            else:
                result.append(char)
        else:
            # Outside string - keep as-is
            result.append(char)

        i += 1

    json_str = ''.join(result)

    # 3. Fix single quotes to double quotes (be careful with this)
    # Only do this if the string looks like it uses single quotes for strings
    if json_str.count("'") > json_str.count('"') * 2:
        # Replace single quotes with double quotes, but not in already quoted strings
        json_str = json_str.replace("'", '"')

    # 4. Remove control characters that might break JSON (except \n, \t, \r which are valid when escaped)
    json_str = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', json_str)

    return json_str


def safe_json_parse(text: str, fallback: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Safely parse JSON with fallback

    Args:
        text: Text to parse
        fallback: Fallback dictionary if parsing fails

    Returns:
        Parsed JSON or fallback
    """
    try:
        return parse_llm_json(text)
    except Exception as e:
        print(f"⚠️  JSON parsing failed: {e}")
        if fallback is not None:
            return fallback
        raise
