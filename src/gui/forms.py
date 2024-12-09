from django import forms

class ContactForm(forms.Form):
    nom = forms.CharField(max_length=100, label="Votre nom")
    email = forms.EmailField(label="Votre email")
    sujet = forms.CharField(max_length=200, label="Sujet")
    message = forms.CharField(widget=forms.Textarea, label="Message")
