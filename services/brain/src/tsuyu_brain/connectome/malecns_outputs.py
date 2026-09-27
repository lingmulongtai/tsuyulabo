"""Explicit additional anatomical output readouts, without inferred valence/signs."""

from __future__ import annotations

# Keep the established MN9, DNa02 and MBON valence pools intact. These outputs
# are separate observations, not aliases for those cells or new plasticity rules.
ADDITIONAL_TYPES = {
    "feeding": ("MN6", "MN11D", "MN11V", "MN12D"),
    "steering": ("DNa01", "DNb05", "DNb06", "DNg13"),
    "grooming": ("DNg11", *(f"DNg12_{suffix}" for suffix in "abcdefgh")),
    "olfaction_mb": tuple(
        f"MBON{i:02}" for i in range(1, 36) if i not in {1, 3, 4, 5, 6, 11, 12, 14}
    ),
}
OUTPUT_REASONS = {
    "feeding": "MN6 extends the labellum; MN11D/V and MN12D observe ingestion/pumping "
    "beyond MN9 (Schwarz et al. 2017; Manzo et al. 2012). Unresolved signs stay excluded.",
    "steering": "DNa01, DNb05/06 and DNg13 correlate with rotational velocity "
    "(Rayshubskiy et al., Fine-grained descending control of steering). Keep soma sides separate.",
    "grooming": "DNg11 front-leg rubbing and DNg12 anterior grooming "
    "(Guo et al. 2022; Cande et al. 2018); retain the release's DNg12_a-h subtypes separately.",
    "olfaction_mb": "Complete exact numbered MBON output census beyond the existing valence "
    "pools. MBON ensemble activity carries learned value (Aso et al. 2014). "
    "No valence is inferred from transmitter or assigned to these additional readouts; "
    "MBON08 is absent and ambiguous '-like' annotations are excluded.",
}

EXTRA_OUTPUTS = tuple(
    group
    for circuit, types in ADDITIONAL_TYPES.items()
    for name in types
    for group in ((f"{name}_L", f"{name}_R") if circuit == "steering" else (name,))
)
