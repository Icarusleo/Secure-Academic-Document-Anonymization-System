from django.db import models
import uuid
from django.db.models import JSONField



class user(models.Model):
    USER_TYPES = [
        ('author','Yazar'),
        ('editor','Editör'),
        ('reviewer','Hakem'),
    ]
    id = models.IntegerField(primary_key=True)
    user_Type = models.CharField(max_length=10,default='author')
    email = models.EmailField(unique=True)
    
    def get_users():
        return user.objects.values_list('email',flat=True)
        
        
class article(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=30)
    article_no = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    article_pdf = models.FileField()
    email = models.EmailField(default='example@gmail.com')
    upload_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20,default='Awaiting review')
    author_message = models.CharField(max_length=100,blank=True, null=True)
    anonymized_pdf = models.FileField(upload_to='anon_pdfs/', null=True, blank=True)  # Eklenen alan
    created_at = models.DateTimeField(auto_now_add=True , null=True, blank=True)
    keywords = models.JSONField(null=True, blank=True)
    encrypted_id = models.CharField(max_length=256, blank=True, null=True)
    final_pdf = models.FileField(upload_to='final_pdfs/', null=True, blank=True)
    
    def return_email(self):
        return self.email
    
class review(models.Model):
    id = models.IntegerField(primary_key=True)
    content = models.CharField(max_length=500)
    article = models.ForeignKey('article', on_delete=models.CASCADE, related_name='reviews',blank=True, null=True)
    
class messages(models.Model):
    id = models.IntegerField(primary_key=True)
    email = models.EmailField(null=False, blank=False) 
    content = models.CharField(max_length=500)
    article = models.ForeignKey('article', on_delete=models.CASCADE, related_name='messages',null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True,null=True, blank=True)

        
class logs(models.Model):
    article = models.ForeignKey('article', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=255)  # "Anonimleştirildi", "Hakem atandı" gibi
    detail = models.TextField(blank=True, null=True)  # opsiyonel açıklama

    def __str__(self):
        return f"[{self.timestamp}] {self.action} (Makale: {self.article.article_no})"
    
class review_assignment(models.Model):
    article = models.ForeignKey(article, on_delete=models.CASCADE)
    email= models.EmailField()
    assigned_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="Atandı")    
    
class Reviewer(models.Model):
    email = models.EmailField()
    name = models.CharField(max_length=100, blank=True)
    interested_subfields = models.JSONField()  # ["Zaman serisi", "AR/VR"]

    def __str__(self):
        return self.email
    
class AnonymizedItem(models.Model):
    article = models.ForeignKey('article', on_delete=models.CASCADE)
    page_number = models.IntegerField()
    rect = JSONField()  # {"x0":..., "y0":..., "x1":..., "y1":...}
    placeholder = models.CharField(max_length=20)
    original_text = models.CharField(max_length=255)