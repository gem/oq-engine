from django import forms


class HazardForm(forms.Form):
    job_config = forms.FileField(label='Job configuration (.ini file)')


class RiskForm(forms.Form):
    job_config = forms.FileField(label='Job configuration (.ini file)')
    hazard_calc = forms.IntegerField(
        required=False,
        label='Hazard calculation ID',
    )
    hazard_result = forms.IntegerField(
        required=False,
        label='Hazard result ID',
    )
