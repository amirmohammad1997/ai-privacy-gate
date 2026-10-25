"""Test Korean PII."""
from app.security.sanitizer.layers.korean import KoreanLayer
from app.security.sanitizer.validators.korean import (
    validate_korean_rrn,
    validate_korean_phone,
)


def main():
    print("=" * 70)
    print("Korean PII Test")
    print("=" * 70)

    # RRN tests (valid format)
    test_rrns = [
        ("900101-1234567", None),  # see checksum
        ("9001011234567", None),
        ("12345-1234567", False),  # too short
    ]

    print("\n--- RRN ---")
    for rrn, expected in test_rrns:
        result = validate_korean_rrn(rrn)
        print(f"  {rrn:20} | valid={result}")

    # Phone tests
    test_phones = [
        ("010-1234-5678", True),
        ("02-1234-5678", True),
        ("+82-10-1234-5678", True),
        ("123", False),
    ]

    print("\n--- Phone ---")
    for phone, expected in test_phones:
        result = validate_korean_phone(phone)
        status = "PASS" if result == expected else "FAIL"
        print(f"{status} | {phone:25} | expected={expected} got={result}")

    print("=" * 70)


if __name__ == "__main__":
    main()