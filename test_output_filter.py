"""Test Output Filter."""
from app.security import PIISanitizer
from app.security.output_filter import OutputFilter, OutputDecision


def main():
    print("=" * 78)
    print("Output Filter Test")
    print("=" * 78)

    sanitizer = PIISanitizer()
    filter_ = OutputFilter(sanitizer)

    test_cases = [
        # (text, expected_decision)
        # ═══ Clean output ═══
        ("Hello! How can I help you today?", OutputDecision.ALLOW),
        ("The capital of France is Paris.", OutputDecision.ALLOW),

        # ═══ Critical secrets → BLOCK ═══
        ("Your API key is sk-abcdefghij1234567890abcdefghij", OutputDecision.BLOCK),
        ("AWS access: AKIAIOSFODNN7EXAMPLE", OutputDecision.BLOCK),
        ("Token: ghp_abcdefghijklmnopqrstuvwxyz0123456789", OutputDecision.BLOCK),

        # ═══ PII leaks → BLOCK (too many) ═══
        ("Emails: a@b.com, c@d.com, e@f.com, g@h.com, i@j.com",
         OutputDecision.BLOCK),

        # ═══ Some PII → REDACT ═══
        ("Contact me at john@example.com", OutputDecision.REDACT),

        # ═══ Entropy leak → REDACT or BLOCK ═══
        ("Here's the token: aB3xK9mP2qL7zX4nR8vT1yU6wS5dF", OutputDecision.REDACT),
    ]

    passed = 0
    failed = 0

    for text, expected in test_cases:
        verdict = filter_.check(text)
        status = "PASS" if verdict.decision == expected else "FAIL"

        if status == "PASS":
            passed += 1
        else:
            failed += 1

        print(f"\n{status} | {text[:60]}")
        print(f"      Expected: {expected.value}")
        print(f"      Got: {verdict.decision.value}")
        print(f"      Reason: {verdict.reason}")
        if verdict.safe_text != text:
            print(f"      Redacted: {verdict.safe_text[:60]}")

    print("\n" + "=" * 78)
    print(f"Results: {passed}/{len(test_cases)} passed, {failed} failed")
    print("=" * 78)


if __name__ == "__main__":
    main()