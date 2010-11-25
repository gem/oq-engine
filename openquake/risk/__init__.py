"""
Core computation methods for the risk 'engine'
These include Classical PSHA-based risk analysis,
and deterministic analysis based on either a set of GMF files,
or a single GMF file."""

# risk tokens
CONDITIONAL_LOSS_KEY_TOKEN = 'loss_conditional'
EXPOSURE_KEY_TOKEN = 'exposure'
GMF_KEY_TOKEN = 'gmf'
LOSS_RATIO_CURVE_KEY_TOKEN = 'loss_ratio_curve'
LOSS_CURVE_KEY_TOKEN = 'loss_curve'
