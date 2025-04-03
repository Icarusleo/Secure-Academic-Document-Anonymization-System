from django import forms 
from . import models

class ArticleForm(forms.ModelForm):
    class Meta:
        model = models.article
        fields = ['email','article_pdf','author_message']
        
        
class ArticleQuerryForm(forms.Form):
    tracking_number = forms.UUIDField(label='Tracking Number')
    email = forms.EmailField(label='E-Mail')
    
class MessageForm(forms.Form):
    #email = forms.EmailField(label="E-Mail:")
    message = forms.CharField(label="Send a message to the editor:", widget=forms.Textarea)
    article_id = forms.IntegerField(widget=forms.HiddenInput())
    
class MessageFormAdmin(forms.Form):
    message = forms.CharField(label="Send a message to the editor:", widget=forms.Textarea)
    article_id = forms.IntegerField(widget=forms.HiddenInput())

    
class AnonSelectForm(forms.Form):
   names = forms.MultipleChoiceField(
       widget=forms.CheckboxSelectMultiple,
       required=False
   )
   emails = forms.MultipleChoiceField(
       widget=forms.CheckboxSelectMultiple,
       required=False
   )
   universities = forms.MultipleChoiceField(
       widget=forms.CheckboxSelectMultiple,
       required=False
   )
   def __init__(self, *args, **kwargs):
       dynamic_data = kwargs.pop("dynamic_data", {})
       super().__init__(*args, **kwargs)
       self.fields['names'].choices = [(x, x) for x in dynamic_data.get("names", [])]
       self.fields['emails'].choices = [(x, x) for x in dynamic_data.get("emails", [])]
       self.fields['universities'].choices = [(x, x) for x in dynamic_data.get("universities", [])]       
    
class ReviewerAssignForm(forms.Form):
    reviewer_email = forms.EmailField(label="Hakem E-posta")