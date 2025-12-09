# evaluator/views.py

from django.shortcuts import render, redirect, get_object_or_404
from .models import Submission, KeyAnswer
from .hwr_service import recognize_handwriting
from .evaluation_service import generate_score_and_feedback
from django.conf import settings
import os

# --- 1. General Views ---

def home_view(request):
    """The main landing page with navigation options."""
    return render(request, 'evaluator/home.html')

# --- 2. Faculty/Evaluator Workflow ---

def faculty_dashboard(request):
    """Dashboard for faculty: shows options to add key answers or start grading."""
    key_answers = KeyAnswer.objects.all()
    context = {'key_answers': key_answers}
    return render(request, 'evaluator/faculty_dashboard.html', context)

def upload_submission(request):
    """Handles image upload and initiates HWR/Evaluation."""
    if request.method == 'POST':
        student_name = request.POST.get('student_name')
        question_id = request.POST.get('question_id')
        answer_file = request.FILES.get('answer_sheet')
        
        if not all([student_name, question_id, answer_file]):
            key_answers = KeyAnswer.objects.all()
            return render(request, 'evaluator/upload_submission.html', {'error': 'Missing form data.', 'key_answers': key_answers})

        key_answer = get_object_or_404(KeyAnswer, pk=question_id)
        submission = Submission(
            student_name=student_name,
            related_question=key_answer,
            answer_sheet_image=answer_file
        )
        submission.save()

        # Run HWR
        extracted_text = recognize_handwriting(submission.answer_sheet_image.name)
        submission.extracted_text = extracted_text
        
        # Run Evaluation
        final_score, feedback_text, metrics = generate_score_and_feedback(
            student_text=submission.extracted_text,
            master_text=key_answer.master_answer,
            mandatory_keywords=key_answer.keywords,
            max_marks=key_answer.max_marks,
        )
        
        submission.score = final_score
        submission.feedback = feedback_text
        submission.save()

        return redirect('view_results', submission_id=submission.id)
    
    key_answers = KeyAnswer.objects.all()
    return render(request, 'evaluator/upload_submission.html', {'key_answers': key_answers})


def view_results(request, submission_id):
    """Shows detailed evaluation metrics (visible to Faculty) with Canvas."""
    submission = get_object_or_404(Submission, pk=submission_id)
    key_answer = submission.related_question
    
    if not submission.extracted_text or submission.extracted_text.startswith("ERROR"):
        context = {'submission': submission, 'status': submission.extracted_text or 'HWR failed.'}
        return render(request, 'evaluator/view_results.html', context)

    # Re-run calculation to get the live metrics dictionary for display
    _, _, metrics = generate_score_and_feedback(
        student_text=submission.extracted_text,
        master_text=key_answer.master_answer,
        mandatory_keywords=key_answer.keywords,
        max_marks=key_answer.max_marks,
    )

    context = {
        'submission': submission,
        'key_answer': key_answer,
        'metrics': metrics,
        'status': 'Evaluation Complete!',
        'image_url': submission.answer_sheet_image.url
    }
    return render(request, 'evaluator/view_results.html', context)


# --- 3. Student Workflow ---

def student_check_results(request):
    """Student enters name and question to find results."""
    submissions = None
    if request.method == 'POST':
        student_name = request.POST.get('student_name', '').strip()
        question_id = request.POST.get('question_id')

        submissions = Submission.objects.filter(student_name__iexact=student_name, related_question__id=question_id).order_by('-id')
        
        if submissions.count() == 1:
            return redirect('student_report_view', submission_id=submissions.first().id)
        
    key_answers = KeyAnswer.objects.all()
    context = {
        'key_answers': key_answers, 
        'submissions': submissions
    }
    return render(request, 'evaluator/student_check_results.html', context)

def student_report_view(request, submission_id):
    """Shows simplified result, feedback, and student's submitted answer (visible to Student)."""
    submission = get_object_or_404(Submission, pk=submission_id)
    key_answer = submission.related_question

    context = {
        'submission': submission,
        'key_answer': key_answer,
        # Pass necessary data directly from submission object
        # The .url attribute gives the browser-accessible path to the image
        'image_url': submission.answer_sheet_image.url, 
        'extracted_text': submission.extracted_text, 
    }
    return render(request, 'evaluator/student_report_view.html', context)