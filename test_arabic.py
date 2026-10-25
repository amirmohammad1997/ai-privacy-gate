"""Test Arabic PII."""
from app.security.sanitizer.layers.arabic import ArabicLayer
from app.security.sanitizer.validators.arabic import (
    validate_saudi_national_id,
    validate_egyptian_national_id,
    validate_uae_emirates_id,
    validate_arabic_mobile,
)


def main():
    print("=" * 70)
    print("Arabic PII Test")
    print("=" * 70)

    # Saudi National ID
    print("\n--- Saudi National ID ---")
    test_ids = ["1234567890", "2345678901"]
    for sid in test_ids:
        result = validate_saudi_national_id(sid)
        print(f"  {sid:15} | valid={result}")

    # Egyptian National ID
    print("\n--- Egyptian National ID ---")
    test_ids = ["29001011234567", "29512311234567"]
    for eid in test_ids:
        result = validate_egyptian_national_id(eid)
        print(f"  {eid:15} | valid={result}")

    # UAE Emirates ID
    print("\n--- UAE Emirates ID ---")
    test_ids = ["784199012345671", "784-1990-1234567-1"]
    for eid in test_ids:
        result = validate_uae_emirates_id(eid)
        print(f"  {eid:25} | valid={result}")

    # Mobile
    print("\n--- Arabic Mobile ---")
    test_phones = [
        "+966512345678",     # Saudi
        "+971501234567",     # UAE
        "+201012345678",     # Egypt
        "0512345678",        # Saudi local
    ]
    for phone in test_phones:
        result = validate_arabic_mobile(phone)
        print(f"  {phone:20} | valid={result}")

    print("=" * 70)


if __name__ == "__main__":
    main()