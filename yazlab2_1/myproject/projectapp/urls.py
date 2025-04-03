from django.urls import path
from . import views

urlpatterns = [
    path('upload-article/', views.upload_article, name='upload_article'),
    path('querry-article/', views.query_article, name='querry_article'),
    path('pdf/', views.example_show_pdf, name='pdf_goster'),
    path('yonetici/', views.admin_panel, name='admin_panel'),
    path('yonetici/makale/<int:pk>/', views.article_detail_admin, name='article_detail_admin'),
    path("api/reviewer-data/", views.reviewer_assignments_api, name="reviewer_data"),
    path("api/submit-review/", views.submit_review, name="submit_review"),
    path("hakem-panel/", views.reviewer_panel, name="reviewer_panel"),
    path('reviewer/<str:email>/', views.reviewer_detail, name='reviewer_detail'),
    path('submit-review/', views.submit_review_form, name='submit_review_form'),
    path('messages/article/<int:article_id>/', views.article_messages_panel, name='article_messages'),
    path('messages/send/', views.send_message, name='send_message'),
    path('send-final/', views.send_final_to_author, name='send_final_to_author'),
    path('cancel-review-to-author',views.cancel_article_review, name ='cancel_review_to_author'),
    path('cancel-review',views.cancel_review, name ='cancel_review'),
    path('cancel-assigment-review',views.cancel_reviewer_assingment, name ='cancel_assigment_review'),
    path('view-pdf/<str:token>/', views.view_pdf_encrypted, name='view_pdf_encrypted'),
    path('update-pdf/', views.update_uploaded_pdf, name='update_uploaded_pdf'),

]
