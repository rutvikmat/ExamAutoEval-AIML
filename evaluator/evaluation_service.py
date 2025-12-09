# evaluator/evaluation_service.py

import re
import numpy as np
import spacy
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import fuzz

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None
    print("WARNING: SpaCy model 'en_core_web_sm' failed to load. Grammar checks disabled.")

STOP_WORDS = set(stopwords.words('english'))

def preprocess(text):
    """Cleans text: lowercase, remove non-alphanumeric, tokenize, remove stop words."""
    if not isinstance(text, str):
        return ""
        
    text = text.lower()
    text = re.sub(r'[^a-z\s]', '', text) 
    
    words = word_tokenize(text)
    
    return " ".join([word for word in words if word not in STOP_WORDS and len(word) > 1])

def calculate_grammar_accuracy(text):
    """Calculates grammar accuracy based on POS tagging and sentence structure."""
    if not nlp or not text.strip():
        return 0.9 
    
    doc = nlp(text)
    content_words = 0
    total_tokens = 0
    
    for token in doc:
        total_tokens += 1
        if token.pos_ in ('NOUN', 'VERB', 'ADJ', 'ADV'):
            content_words += 1
            
    grammar_score = (content_words / total_tokens) if total_tokens else 0
    
    return 0.6 + (grammar_score * 0.4) if grammar_score <= 1.0 else 1.0


def calculate_keyword_order_accuracy(student_text, master_keywords):
    """Measures how closely the mandatory keywords follow the sequence expected."""
    master_keywords = [k.strip().lower() for k in master_keywords.split(',') if k.strip()]
    if len(master_keywords) < 2:
        return 1.0
    
    student_text_lower = student_text.lower()
    keyword_indices = []
    
    for kw in master_keywords:
        try:
            index = student_text_lower.index(kw)
            keyword_indices.append((kw, index))
        except ValueError:
            pass
            
    if len(keyword_indices) < 2:
        return 0.0

    ordered_indices = [item[1] for item in keyword_indices]
    is_in_order = all(ordered_indices[i] <= ordered_indices[i+1] for i in range(len(ordered_indices) - 1))
    
    return 1.0 if is_in_order else 0.0


def calculate_metrics(student_text, master_text, mandatory_keywords):
    """Calculates all new and existing metrics."""
    
    cleaned_student = preprocess(student_text)
    cleaned_master = preprocess(master_text)
    
    if not cleaned_student or not cleaned_master:
        return {
            'keyword_match': 0.0, 'semantic_similarity': 0.0, 'lexical_match': 0.0,
            'matched_keywords_list': [], 'mandatory_keywords': mandatory_keywords, 
            'grammar_accuracy': 0.0, 'keyword_order_accuracy': 0.0, 'cleaned_student_text_len': 0
        }
    
    # 1. Keyword Matching
    master_keywords = [k.strip().lower() for k in mandatory_keywords.split(',') if k.strip()]
    student_words = set(cleaned_student.split())
    matched_keywords = [kw for kw in master_keywords if kw in student_words]
    keyword_match_score = (len(matched_keywords) / len(master_keywords)) if master_keywords else 0.0

    # 2. Semantic Similarity
    documents = [cleaned_master, cleaned_student]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)
    semantic_similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]

    # 3. Lexical Match
    lexical_match_ratio = fuzz.ratio(cleaned_student, cleaned_master) / 100.0
    
    # 4. Grammar and Order Accuracy
    grammar_accuracy = calculate_grammar_accuracy(student_text)
    keyword_order_accuracy = calculate_keyword_order_accuracy(student_text, mandatory_keywords)
    
    return {
        'keyword_match': keyword_match_score,
        'semantic_similarity': semantic_similarity,
        'lexical_match': lexical_match_ratio,
        'grammar_accuracy': grammar_accuracy,
        'keyword_order_accuracy': keyword_order_accuracy,
        'matched_keywords_list': matched_keywords,
        'mandatory_keywords': mandatory_keywords,
        'cleaned_student_text_len': len(cleaned_student.split())
    }

def generate_score_and_feedback(student_text, master_text, mandatory_keywords, max_marks):
    metrics = calculate_metrics(student_text, master_text, mandatory_keywords)
    
    # Define Weights (Total must sum to 1.0)
    W_KEYWORD = 0.25      
    W_SEMANTIC = 0.45     
    W_LEXICAL = 0.10      
    W_GRAMMAR = 0.10      
    W_ORDER = 0.10        
    total_weight = W_KEYWORD + W_SEMANTIC + W_LEXICAL + W_GRAMMAR + W_ORDER

    final_score_percentage = (
        (metrics['keyword_match'] * W_KEYWORD) + 
        (metrics['semantic_similarity'] * W_SEMANTIC) + 
        (metrics['lexical_match'] * W_LEXICAL) +
        (metrics['grammar_accuracy'] * W_GRAMMAR) + 
        (metrics['keyword_order_accuracy'] * W_ORDER)
    ) / total_weight

    final_score = round(final_score_percentage * max_marks, 2)
    
    # --- Feedback Generation ---
    feedback = []
    
    if final_score_percentage < 0.4:
        feedback.append("The answer lacks fundamental concepts and requires substantial revision.")
        
    if metrics['keyword_match'] < 0.7:
        all_master_keywords = [k.strip().lower() for k in metrics['mandatory_keywords'].split(',') if k.strip()]
        missing_keywords = [kw for kw in all_master_keywords if kw not in metrics['matched_keywords_list']]
        if missing_keywords:
            feedback.append(f"Essential concepts/keywords were missing: {', '.join(missing_keywords[:3])}.")
            
    if metrics['semantic_similarity'] < 0.7:
        feedback.append("The overall meaning is conceptually weak; focus on aligning your response with the standard answer.")
        
    if metrics['grammar_accuracy'] < 0.8:
        feedback.append("The response contains several structural/grammatical errors. Focus on sentence construction.")

    if metrics['keyword_order_accuracy'] < 1.0 and len(metrics['mandatory_keywords'].split(',')) >= 2:
        feedback.append("The key steps or sequence of ideas were presented out of order.")

    if final_score < max_marks * 0.8:
        feedback.append(f"Current Score: {final_score}/{max_marks}. Aim for greater detail and precision.")
    else:
        feedback.append("Excellent work! The answer is comprehensive and conceptually sound.")
        
    return final_score, "\n".join(feedback), metrics