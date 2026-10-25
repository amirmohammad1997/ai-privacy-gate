"""Test Japanese PII."""
from app.security.sanitizer.layers.japanese import JapaneseLayer
from app.security.sanitizer.validators.japanese import (
    validate_japanese_my_number,
    validate_japanese_phone,
)


def main():
    print("=" * 70)
    print("Japanese PII Test")
    print("=" * 70)

    # My Number tests
    test_numbers = [
        ("123456789018", None),  # see checksum
        ("1234-5678-9012", None),
        ("12345678901", False),  # too short
    ]

    print("\n--- My Number ---")
    for num, expected in test_numbers:
        result = validate_japanese_my_number(num)
        print(f"  {num:20} | valid={result}")

    # Phone tests
    test_phones = [
        ("090-1234-5678", True),
        ("080-1234-5678", True),
        ("03-1234-5678", True),
        ("+81-90-1234-5678", True),
        ("123", False),
    ]

    print("\n--- Phone ---")
    for phone, expected in test_phones:
        result = validate_japanese_phone(phone)
        status = "PASS" if result == expected else "FAIL"
        print(f"{status} | {phone:25} | expected={expected} got={result}")

    # Layer
    print("\n--- Layer Detection ---")
    layer = JapaneseLayer()
    text = "電話番号は090-1234-5678です"
    entities = layer.detect(text)
    for e in entities:
        print(f"  {e.entity_type.value}: {e.text}")

    print("=" * 70)


if __name__ == "__main__":
    main()