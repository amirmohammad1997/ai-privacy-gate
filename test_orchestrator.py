"""Final test for the complete sanitizer."""
from app.security.sanitizer.orchestrator import PIISanitizer


def main():
    print("=" * 78)
    print("Final Sanitizer Test — All 12 Languages")
    print("=" * 78)

    sanitizer = PIISanitizer()

    # ─── Multi-language tests ───
    test_cases = [
        # (text, expected_language, expected_pii_count_min)
        ("My email is john@example.com and SSN is 234-56-7890", "en", 2),
        ("کد ملی من 0012345672 و موبایلم 09123456789 است", "fa", 2),
        ("TCKN: 10000000146, cep: 0532 123 45 67", "tr", 2),
        ("我的身份证号是11010519491231002X，手机是13812345678", "zh", 2),
        ("電話は090-1234-5678です", "ja", 1),
        ("전화번호는010-1234-5678입니다", "ko", 1),
        ("Mi DNI es 12345678Z y mi móvil +34 612 345 678", "es", 2),
        ("Mon numéro est 06 12 34 56 78", "fr", 1),
        ("Meine Nummer ist 0171 1234567", "de", 1),
        ("CPF: 111.444.777-35", "pt", 1),
        ("Мой телефон +7 912 345 67 89", "ru", 1),
        ("مرحبا، رقمي +966512345678", "ar", 1),
    ]

    passed = 0
    failed = 0

    for text, expected_lang, expected_count in test_cases:
        result = sanitizer.sanitize(text)

        lang_ok = result.detected_language == expected_lang
        count_ok = result.total >= expected_count

        status = "PASS" if (lang_ok and count_ok) else "FAIL"

        if status == "PASS":
            passed += 1
        else:
            failed += 1

        print(f"\n{status} | {text[:55]}")
        print(f"      Lang:  expected={expected_lang:3}  got={result.detected_language:3}")
        print(f"      PII:   expected>={expected_count}   got={result.total}")
        if result.by_type:
            print(f"      Types: {result.by_type}")

    # ─── Round-trip test ───
    print("\n" + "=" * 78)
    print("Round-trip test (sanitize → restore)")
    print("=" * 78)

    original = "Mi DNI es 12345678Z y mi móvil es +34 612 345 678"
    result = sanitizer.sanitize(original)
    restored = sanitizer.restore(result.sanitized_text, result.mapping)

    roundtrip_ok = restored == original

    print(f"\nOriginal:  {original}")
    print(f"Sanitized: {result.sanitized_text}")
    print(f"Restored:  {restored}")
    print(f"\nRound-trip: {'✅ PASS' if roundtrip_ok else '❌ FAIL'}")

    # ─── Summary ───
    print("\n" + "=" * 78)
    print(f"Results: {passed}/{len(test_cases)} passed, {failed} failed")
    print("=" * 78)


if __name__ == "__main__":
    main()