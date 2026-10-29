from django import forms

from .models import TieuChiUuTien


class TieuChiUuTienForm(forms.ModelForm):
    class Meta:
        model = TieuChiUuTien
        fields = ("ca_uu_tien", "so_ngay_hoc_toi_da", "han_che_tiet_trong")
        widgets = {
            "ca_uu_tien": forms.Select(attrs={"class": "form-select"}),
            "so_ngay_hoc_toi_da": forms.NumberInput(
                attrs={"class": "form-control", "min": 1, "max": 6}
            ),
            "han_che_tiet_trong": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
