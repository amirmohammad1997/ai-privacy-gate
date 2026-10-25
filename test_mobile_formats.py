"""Test Persian mobile phone formats."""
from app.security.sanitizer.layers.persian import PersianLayer


def main():
    layer = PersianLayer()

    formats = [
        ("+989145872154",        "with +98"),
        ("+98 914 587 2154",     "with +98 and spaces"),
        ("+98-914-587-2154",     "with +98 and dashes"),
        ("00989145872154",       "with 0098"),
        ("0098 914 587 2154",    "with 0098 and spaces"),
        ("989145872154",         "with 98 only"),
        ("09145872154",          "local with 0"),
        ("0914 587 2154",        "local with 0 and spaces"),
        ("0914-587-2154",        "local with 0 and dashes"),
        ("9145872154",           "without 0 and country code"),
        ("۰۹۱۴۵۸۷۲۱۵۴",         "Persian digits with 0"),
        ("+۹۸۹۱۴۵۸۷۲۱۵۴",        "Persian digits with +98"),
        ("۰۰۹۸۹۱۴۵۸۷۲۱۵۴",      "Persian digits with 0098"),
    ]

    print("=" * 70)
    print("Persian Mobile Phone Format Test")
    print("=" * 70)
    print()

    passed = 0
    failed = 0

    for fmt, description in formats:
        text = f"شماره من {fmt} است"
        entities = layer.detect(text)

        if entities:
            entity = entities[0]
            print(f"OK   | {fmt:25} | {description:35} | {entity.entity_type.value}")
            passed += 1
        else:
            print(f"FAIL | {fmt:25} | {description:35} | NOT DETECTED")
            failed += 1

    print()
    print("=" * 70)
    print(f"Passed: {passed}/{len(formats)}")
    print(f"Failed: {failed}/{len(formats)}")
    print("=" * 70)


if __name__ == "__main__":
    main()