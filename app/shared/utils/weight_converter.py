"""
Utilidad de conversión de unidades de peso.
La unidad base del sistema es el KILOGRAMO (kg).
"""
from decimal import Decimal
from app.shared.constants.roles import WeightUnit


# Factores de conversión desde kilogramos
KG_TO_LB = Decimal("2.20462262185")
KG_TO_TON = Decimal("0.001")
KG_TO_OZ = Decimal("35.2739619496")

# Factores de conversión a kilogramos
LB_TO_KG = Decimal("0.45359237")
TON_TO_KG = Decimal("1000")
OZ_TO_KG = Decimal("0.0283495231")


def kg_to_unit(kg_value: Decimal | float, target_unit: WeightUnit) -> Decimal:
    """Convierte kilogramos a la unidad de destino."""
    value = Decimal(str(kg_value))
    conversions = {
        WeightUnit.KILOGRAMOS: value,
        WeightUnit.LIBRAS: value * KG_TO_LB,
        WeightUnit.TONELADAS: value * KG_TO_TON,
        WeightUnit.ONZAS: value * KG_TO_OZ,
    }
    return round(conversions[target_unit], 6)


def unit_to_kg(value: Decimal | float, source_unit: WeightUnit) -> Decimal:
    """Convierte desde cualquier unidad a kilogramos."""
    val = Decimal(str(value))
    conversions = {
        WeightUnit.KILOGRAMOS: val,
        WeightUnit.LIBRAS: val * LB_TO_KG,
        WeightUnit.TONELADAS: val * TON_TO_KG,
        WeightUnit.ONZAS: val * OZ_TO_KG,
    }
    return round(conversions[source_unit], 6)


def convert_weight(
    value: Decimal | float,
    from_unit: WeightUnit,
    to_unit: WeightUnit,
) -> Decimal:
    """Convierte un valor de una unidad a otra."""
    kg = unit_to_kg(value, from_unit)
    return kg_to_unit(kg, to_unit)


def weight_summary(kg_value: Decimal | float) -> dict:
    """Devuelve un resumen del peso en todas las unidades."""
    return {
        "kg": float(kg_to_unit(kg_value, WeightUnit.KILOGRAMOS)),
        "lb": float(kg_to_unit(kg_value, WeightUnit.LIBRAS)),
        "ton": float(kg_to_unit(kg_value, WeightUnit.TONELADAS)),
        "oz": float(kg_to_unit(kg_value, WeightUnit.ONZAS)),
    }
