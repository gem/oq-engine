from openquake.commonlib.calculators import calculators, base

@calculators.add('classical')
class ClassicalCalculator(base.BaseCalculator):
    """
    Classical PSHA calculator
    """
    def pre_execute(self):
        pass

    def execute(self):
        pass

    def post_execute(self, result):
        pass


@calculators.add('classical_risk')
class ClassicalCalculator(base.BaseRiskCalculator):
    """
    Classical Risk calculator
    """
    def post_execute(self, result):
        return {}
