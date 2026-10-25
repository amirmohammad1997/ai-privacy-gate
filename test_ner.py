"""Test NER Layer."""
from app.security.sanitizer.orchestrator import PIISanitizer


def main():
    print("=" * 78)
    print("NER Layer Test")
    print("=" * 78)

    sanitizer = PIISanitizer()

    test_cases = [
        "My name is John Doe and I live in New York",
        "I work at Google in California",
        "Sarah Johnson called from Microsoft headquarters",
        "Barack Obama was born in Hawaii",
        "Elon Musk founded Tesla and SpaceX",
        "The Eiffel Tower is in Paris, France",
        "My email is john@example.com and I live in London",
        "Dr. Smith works at Johns Hopkins Hospital in Baltimore",
    ]

    for text in test_cases:
        result = sanitizer.sanitize(text)
        print(f"\nText: {text}")
        print(f"  Language: {result.detected_language}")
        print(f"  PII detected: {result.total}")
        if result.by_type:
            print(f"  Types: {result.by_type}")
        print(f"  Sanitized: {result.sanitized_text}")

    # Round-trip test
    print("\n" + "=" * 78)
    print("Round-trip Test")
    print("=" * 78)

    original = "John Doe works at Google in New York"
    result = sanitizer.sanitize(original)
    restored = sanitizer.restore(result.sanitized_text, result.mapping)

    print(f"\nOriginal:  {original}")
    print(f"Sanitized: {result.sanitized_text}")
    print(f"Restored:  {restored}")
    print(f"Round-trip: {'✅ PASS' if restored == original else '❌ FAIL'}")


if __name__ == "__main__":
    main()