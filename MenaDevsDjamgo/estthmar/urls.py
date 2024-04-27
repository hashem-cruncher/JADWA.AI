from django.urls import path
from .views import home, AIView, AskPDFView, pdf_upload, PDFUploadAPI  # Import PDFUploadAPI

urlpatterns = [
    path('', home, name='home'),
    path('api/ai/', AIView.as_view(), name='api-ai'),
    path('api/ask_pdf/', AskPDFView.as_view(), name='ask_pdf'),
    path('upload_pdf/', pdf_upload, name='upload_pdf'),
    path('api/upload_pdf/', PDFUploadAPI.as_view(), name='api-upload-pdf'),  # API endpoint for uploading PDF
]
