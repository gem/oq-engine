"""
Top-level managers for hazard computation.
"""

from opengem import java

def run_hazard():
    jvm = java.jvm()
    GemComputeModel = jvm.JClass(
        "org.opensha.gem.GEM1.calc.gemHazardCalculator.GemComputeModel")
    
    # Build source list
    input_model = jvm.JClass()
    
    engine = GemComputeModel(model.getList(), modelName,
                gmpeLogicTree.getGemLogicTree(), latmin, latmax, lonmin,
                lonmax, delta, probLevel, outDir, outputHazCurve, calcSet);
