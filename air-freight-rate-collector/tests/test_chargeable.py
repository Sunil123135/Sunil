from src.collectors.freightos_quotes import chargeable_weight_kg, parse_usd_per_kg


def test_chargeable_uses_actual_when_dense():
    assert chargeable_weight_kg(300, 60, 60, 60) == 300


def test_chargeable_uses_volumetric_when_light():
    # 100x100x100 / 6000 = 166.67 > 50
    assert abs(chargeable_weight_kg(50, 100, 100, 100) - 166.6666667) < 1e-6


def test_parse_midpoint():
    payload = {
        "response": {
            "estimatedFreightRates": {
                "numQuotes": 1,
                "mode": {
                    "price": {
                        "min": {"moneyAmount": {"amount": 300, "currency": "USD"}},
                        "max": {"moneyAmount": {"amount": 500, "currency": "USD"}},
                    },
                    "transitTimes": {"min": 2, "max": 5},
                },
            }
        }
    }
    parsed = parse_usd_per_kg(payload, 100)
    assert parsed["usd_per_kg_min"] == 3.0
    assert parsed["usd_per_kg_max"] == 5.0
    assert parsed["usd_per_kg_mid"] == 4.0
