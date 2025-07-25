import pandas as pd
from toolkits.db import run_query

def update_student_progress_completion(assignment_id=None, student_email=None, question_id=None):
    """
    Update is_completed field in hackathon_2025_student_progress based on actual submissions
    
    Args:
        assignment_id: Optional - update for specific assignment
        student_email: Optional - update for specific student
        question_id: Optional - update for specific question
    """
    
    # Build WHERE clause based on parameters
    where_conditions = []
    if assignment_id:
        where_conditions.append(f"sp.assignment_id = {assignment_id}")
    if student_email:
        where_conditions.append(f"sp.student_email = '{student_email}'")
    if question_id:
        where_conditions.append(f"sp.question_id = {question_id}")
    
    where_clause = "WHERE " + " AND ".join(where_conditions) if where_conditions else ""
    
    # Get all progress records that need checking
    progress_query = f"""
    SELECT sp.id, sp.assignment_id, sp.student_email, sp.question_id,
           cm.user_id, q.type as question_type
    FROM hackathon_2025_student_progress sp
    JOIN hackathon_2025_class_members cm ON sp.student_email = cm.email
    JOIN hackathon_2025_assignment_questions aq ON sp.assignment_id = aq.assignment_id 
        AND sp.question_id = aq.question_id
    JOIN questions q ON sp.question_id = q.id
    {where_clause}
    """
    
    try:
        progress_records = run_query(progress_query)
        
        if progress_records.empty:
            return {"updated": 0, "errors": 0}
        
        updated_count = 0
        error_count = 0
        
        for _, record in progress_records.iterrows():
            try:
                user_id = record['user_id']
                question_id = record['question_id']
                question_type = record['question_type']
                progress_id = record['id']
                
                is_completed = False
                score = 0
                attempts = 0
                
                if question_type in ['coding', 'algorithm']:
                    # Check coding submissions
                    code_query = f"""
                    SELECT COUNT(*) as attempts, MAX(is_accepted) as accepted
                    FROM user_code_runs 
                    WHERE user_id = {user_id} AND question_id = {question_id}
                    """
                    code_result = run_query(code_query)
                    
                    if not code_result.empty:
                        attempts = code_result.iloc[0]['attempts']
                        is_completed = bool(code_result.iloc[0]['accepted'])
                        score = 1.0 if is_completed else 0
                        
                else:
                    # Check text submissions
                    text_query = f"""
                    SELECT MAX(score) as max_score, COUNT(*) as attempts
                    FROM text_submissions 
                    WHERE user_id = {user_id} AND question_id = {question_id}
                    """
                    text_result = run_query(text_query)
                    
                    if not text_result.empty and text_result.iloc[0]['max_score'] is not None:
                        score = text_result.iloc[0]['max_score']
                        attempts = text_result.iloc[0]['attempts']
                        is_completed = score >= 0.8
                
                # Update the progress record
                update_query = f"""
                UPDATE hackathon_2025_student_progress 
                SET is_completed = {1 if is_completed else 0},
                    score = {score},
                    attempts = {attempts},
                    last_updated = NOW()
                WHERE id = {progress_id}
                """
                run_query(update_query)
                updated_count += 1
                
            except Exception as e:
                print(f"Error updating progress record {record['id']}: {e}")
                error_count += 1
                
        return {
            "updated": updated_count, 
            "errors": error_count,
            "total": len(progress_records)
        }
        
    except Exception as e:
        print(f"Error in update_student_progress_completion: {e}")
        return {"updated": 0, "errors": 1, "error_message": str(e)}


def update_completion_on_submission(user_id, question_id, is_accepted=None, score=None):
    """
    Update completion status when a new submission is made
    This should be called after inserting into user_code_runs or text_submissions
    
    Args:
        user_id: The user who made the submission
        question_id: The question that was submitted
        is_accepted: For coding questions - whether the solution was accepted
        score: For text questions - the score received
    """
    
    # Get student email from user_id
    email_query = f"""
    SELECT email FROM hackathon_2025_class_members 
    WHERE user_id = {user_id}
    LIMIT 1
    """
    email_result = run_query(email_query)
    
    if email_result.empty:
        return {"error": "Student email not found"}
    
    student_email = email_result.iloc[0]['email']
    
    # Update all assignments that include this question for this student
    update_query = f"""
    UPDATE hackathon_2025_student_progress sp
    JOIN hackathon_2025_assignment_questions aq ON sp.assignment_id = aq.assignment_id 
        AND sp.question_id = aq.question_id
    SET sp.is_completed = {1 if (is_accepted or (score and score >= 0.8)) else 0},
        sp.score = {score if score is not None else (1.0 if is_accepted else 0)},
        sp.attempts = sp.attempts + 1,
        sp.last_updated = NOW()
    WHERE sp.student_email = '{student_email}' AND sp.question_id = {question_id}
    """
    
    try:
        run_query(update_query)
        return {"success": True, "student_email": student_email, "question_id": question_id}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Example: Update all completion statuses
    result = update_student_progress_completion()
    print(f"Updated {result['updated']} records with {result['errors']} errors")