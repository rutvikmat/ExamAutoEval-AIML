from django.db import models

class KeyAnswer(models.Model):
    question_text = models.CharField(max_length=500)
    master_answer = models.TextField()
    keywords = models.TextField(help_text="Comma-separated mandatory keywords")
    max_marks = models.IntegerField(default=10)

    def __str__(self):
        return self.question_text[:50]

class Submission(models.Model):
    student_name = models.CharField(max_length=100)
    answer_sheet_image = models.ImageField(upload_to='answer_sheets/')
    related_question = models.ForeignKey(KeyAnswer, on_delete=models.CASCADE)
    
    extracted_text = models.TextField(blank=True, null=True)
    
    score = models.FloatField(default=0.0)
    feedback = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.student_name} - {self.related_question.question_text[:20]}"