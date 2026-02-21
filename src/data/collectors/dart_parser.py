"""DART API response parser."""

import xml.etree.ElementTree as ET

from src.data.collectors.dart_errors import (
    DartAPIError,
    DartNoDataError,
    DartRateLimitError,
)


def parse_dart_response(response_json: dict) -> list[dict]:
    """Parse DART API response and handle status codes.

    DART API always returns HTTP 200, so error detection is based on the
    'status' field in the JSON response.

    Args:
        response_json: DART API JSON response

    Returns:
        list[dict]: Response data list

    Raises:
        DartNoDataError: If status is 013 (no data)
        DartRateLimitError: If status is 020 (rate limit exceeded)
        DartAPIError: For other error statuses
    """
    status = response_json.get("status", "")
    message = response_json.get("message", "")

    if status == "000":
        return response_json.get("list", [])  # type: ignore[no-any-return]
    elif status == "013":
        raise DartNoDataError(f"No data: {message}", status=status)
    elif status == "020":
        raise DartRateLimitError(f"Rate limit exceeded: {message}", status=status)
    else:
        raise DartAPIError(f"DART API error [{status}]: {message}", status=status)


def parse_corp_code_xml(xml_bytes: bytes) -> dict[str, str]:
    """Parse corpCode.xml and return stock_code to corp_code mapping.

    Only listed companies (with non-empty stock_code) are included.

    Args:
        xml_bytes: corpCode.xml file content (bytes)

    Returns:
        dict[str, str]: {stock_code: corp_code} mapping for listed companies
    """
    root = ET.fromstring(xml_bytes)
    mapping: dict[str, str] = {}

    for item in root.findall(".//list"):
        corp_code_elem = item.find("corp_code")
        stock_code_elem = item.find("stock_code")

        if corp_code_elem is not None and stock_code_elem is not None:
            stock_code = stock_code_elem.text or ""
            corp_code = corp_code_elem.text or ""

            if stock_code.strip():
                mapping[stock_code.strip()] = corp_code.strip()

    return mapping
