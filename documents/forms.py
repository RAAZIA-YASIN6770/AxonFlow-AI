from django import forms
from .models import Document

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Document Title'}),
            'file': forms.FileInput(attrs={'class': 'form-file-input'}),
        }
