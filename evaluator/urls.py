from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'), 

    # Faculty/Evaluator Workflow
    path('faculty/', views.faculty_dashboard, name='faculty_dashboard'),
    path('faculty/upload/', views.upload_submission, name='upload_submission'),
    path('faculty/results/<int:submission_id>/', views.view_results, name='view_results'),

    # Student Workflow
    path('student/check/', views.student_check_results, name='student_check_results'),
    path('student/report/<int:submission_id>/', views.student_report_view, name='student_report_view'),
]