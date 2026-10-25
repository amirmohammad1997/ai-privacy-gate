"""Test Chinese PII."""
from app.security.sanitizer.layers.chinese import ChineseLayer
from app.security.sanitizer.validators.chinese import (
    validate_chinese_id,
    validate_chinese_phone,
)


def main():
    print("=" * 70)
    print("Chinese PII Test")
    print("=" * 70)

    # Valid Chinese ID examples
    test_ids = [
        ("11010519491231002X", True),
        ("440524188001010014", True),
        ("12345678901234567X", False),  # invalid checksum
        ("110105194912310021", False),  # wrong checksum
    ]

    print("\n--- ID Card ---")
    for id_num, expected in test_ids:
        result = validate_chinese_id(id_num)
        status = "PASS" if result == expected else "FAIL"
        print(f"{status} | {id_num:20} | expected={expected} got={result}")

    # Phone tests
    test_phones = [
        ("13812345678", True),
        ("+8613812345678", True),
        ("008613812345678", True),
        ("138-1234-5678", True),
        ("1234567890", False),
    ]

    print("\n--- Phone ---")
    for phone, expected in test_phones:
        result = validate_chinese_phone(phone)
        status = "PASS" if result == expected else "FAIL"
        print(f"{status} | {phone:20} | expected={expected} got={result}")

    # Layer test
    print("\n--- Layer Detection ---")
    layer = ChineseLayer()
    text = "我的身份证号是11010519491231002X，手机号是13812345678"
    entities = layer.detect(text)
    for e in entities:
        print(f"  {e.entity_type.value}: {e.text}")

    print("=" * 70)


if __name__ == "__main__":
    main()