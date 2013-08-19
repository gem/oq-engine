from django import forms


class HazardForm(forms.Form):
    job_config = forms.FileField(label='Job configuration (.ini file)')
