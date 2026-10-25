"""Test European PII."""
from app.security.sanitizer.layers.spanish import SpanishLayer
from app.security.sanitizer.layers.french import FrenchLayer
from app.security.sanitizer.layers.german import GermanLayer
from app.security.sanitizer.layers.portuguese import PortugueseLayer
from app.security.sanitizer.layers.russian import RussianLayer


def main():
    print("=" * 70)
    print("European PII Test")
    print("=" * 70)

    # ─── Spanish ───
    print("\n--- Spanish ---")
    es = SpanishLayer()
    test_texts = [
        "Mi DNI es 12345678Z",
        "Mi NIE es X1234567L",
        "Móvil: +34 612 345 678",
    ]
    for text in test_texts:
        entities = es.detect(text)
        if entities:
            for e in entities:
                print(f"  OK   | {text[:40]:40} | {e.entity_type.value}: {e.text}")
        else:
            print(f"  FAIL | {text[:40]:40} | (nothing)")

    # ─── French ───
    print("\n--- French ---")
    fr = FrenchLayer()
    test_texts = [
        "Mon téléphone est 06 12 34 56 78",
        "Mobile: +33 7 12 34 56 78",
    ]
    for text in test_texts:
        entities = fr.detect(text)
        if entities:
            for e in entities:
                print(f"  OK   | {text[:40]:40} | {e.entity_type.value}: {e.text}")
        else:
            print(f"  FAIL | {text[:40]:40} | (nothing)")

    # ─── German ───
    print("\n--- German ---")
    de = GermanLayer()
    test_texts = [
        "Meine Handynummer ist 0171 1234567",
        "Tel: +49 30 12345678",
    ]
    for text in test_texts:
        entities = de.detect(text)
        if entities:
            for e in entities:
                print(f"  OK   | {text[:40]:40} | {e.entity_type.value}: {e.text}")
        else:
            print(f"  FAIL | {text[:40]:40} | (nothing)")

    # ─── Portuguese ───
    print("\n--- Portuguese/Brazilian ---")
    pt = PortugueseLayer()
    # Valid CPF example: 111.444.777-35
    test_texts = [
        "CPF: 111.444.777-35",
        "Tel: +55 11 98765-4321",
    ]
    for text in test_texts:
        entities = pt.detect(text)
        if entities:
            for e in entities:
                print(f"  OK   | {text[:40]:40} | {e.entity_type.value}: {e.text}")
        else:
            print(f"  FAIL | {text[:40]:40} | (nothing)")

    # ─── Russian ───
    print("\n--- Russian ---")
    ru = RussianLayer()
    test_texts = [
        "Мой телефон +7 912 345 67 89",
        "Мобильный: 8-912-345-67-89",
    ]
    for text in test_texts:
        entities = ru.detect(text)
        if entities:
            for e in entities:
                print(f"  OK   | {text[:40]:40} | {e.entity_type.value}: {e.text}")
        else:
            print(f"  FAIL | {text[:40]:40} | (nothing)")

    print("=" * 70)


if __name__ == "__main__":
    main()