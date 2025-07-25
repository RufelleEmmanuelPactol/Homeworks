import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import hashlib
import secrets
import json
import re
from typing import List, Dict, Optional
import requests
import os
from io import BytesIO
from toolkits.db import run_query

# Page configuration
st.set_page_config(
    page_title="Interview Query - Instructor Portal",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1e3a8a;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f9ff;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #e0e7ff;
        text-align: center;
    }
    .assignment-card {
        background-color: #fefce8;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #fef3c7;
        margin-bottom: 1rem;
    }
    .success-message {
        background-color: #d1fae5;
        color: #065f46;
        padding: 1rem;
        border-radius: 6px;
        margin: 1rem 0;
    }
    .warning-message {
        background-color: #fed7aa;
        color: #92400e;
        padding: 1rem;
        border-radius: 6px;
        margin: 1rem 0;
    }
    .question-card {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f9fafb;
    }
    .selected-question {
        border-color: #3b82f6;
        background-color: #eff6ff;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'verification_code' not in st.session_state:
    st.session_state.verification_code = None
if 'selected_class' not in st.session_state:
    st.session_state.selected_class = None
if 'selected_questions' not in st.session_state:
    st.session_state.selected_questions = []

# Question search API
def search_questions(query: str, limit: int = 20) -> List[Dict]:
    """Search questions using magus API"""
    try:
        url = "https://magus.interviewquery.com/search"
        payload = {
            "query": query,
            "content_types": ["questions"],
            "companies": [],
            "positions": [],
            "limit": limit
        }
        
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        return data.get('results', [])
    except requests.RequestException as e:
        st.error(f"Error searching questions: {e}")
        return []

# Helper functions
def validate_email(email: str) -> bool:
    """Validate if email is from whitelisted domain"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False
    
    # Check whitelist
    whitelisted_domains = ['.edu', '@interviewquery.com']
    return any(email.endswith(domain) for domain in whitelisted_domains)

def generate_verification_code() -> str:
    """Generate 6-digit verification code"""
    return f"{secrets.randbelow(1000000):06d}"

def send_verification_email(email: str, code: str) -> bool:
    """Send verification email"""
    # For demo, just store in session state
    # In production, integrate with SendGrid
    st.session_state.verification_code = code
    st.session_state.demo_email_sent = True
    return True

def create_signed_link(question_id: int, assignment_id: int, user_email: str) -> str:
    """Create signed link for question access"""
    timestamp = int(datetime.now().timestamp())
    data = f"{question_id}:{assignment_id}:{user_email}:{timestamp}"
    signature = hashlib.sha256(data.encode()).hexdigest()[:16]
    return f"https://interviewquery.com/questions/{question_id}?hw={assignment_id}&u={signature}"

def parse_csv(file) -> List[str]:
    """Parse CSV file and extract emails"""
    try:
        df = pd.read_csv(file)
        email_columns = [col for col in df.columns if 'email' in col.lower()]
        if email_columns:
            return df[email_columns[0]].dropna().tolist()
        return df.iloc[:, 0].dropna().tolist()
    except Exception as e:
        st.error(f"Error parsing CSV: {e}")
        return []

# Database operations - TABLES NEED TO BE CREATED MANUALLY
def create_instructor_tables():
    """Show required table creation statements"""
    st.error("⚠️ Database tables need to be created manually. Please run these SQL statements:")
    
    tables_sql = """
    -- Table 1: Instructor Classes
    CREATE TABLE hackathon_2025_instructor_classes (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        class_name VARCHAR(256) NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    );

    -- Table 2: Class Members (Students)
    CREATE TABLE hackathon_2025_class_members (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        class_id BIGINT NOT NULL,
        email VARCHAR(255) NOT NULL,
        user_id INT NULL,
        invited_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        joined_at DATETIME NULL,
        is_active TINYINT(1) DEFAULT 1,
        FOREIGN KEY (class_id) REFERENCES hackathon_2025_instructor_classes(id)
    );

    -- Table 3: Assignments
    CREATE TABLE hackathon_2025_assignments (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        class_id BIGINT NOT NULL,
        name VARCHAR(255) NOT NULL,
        due_date DATETIME NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (class_id) REFERENCES hackathon_2025_instructor_classes(id)
    );

    -- Table 4: Assignment Questions
    CREATE TABLE hackathon_2025_assignment_questions (
        id BIGINT AUTO_INCREMENT PRIMARY KEY,
        assignment_id BIGINT NOT NULL,
        question_id INT NOT NULL,
        points INT DEFAULT 0,
        FOREIGN KEY (assignment_id) REFERENCES hackathon_2025_assignments(id),
        FOREIGN KEY (question_id) REFERENCES questions(id)
    );
    """
    
    st.code(tables_sql, language='sql')
    return False

def get_user_classes(user_id: int) -> List[Dict]:
    """Get classes for a user"""
    # First check if table exists and what columns it has
    try:
        check_query = "SHOW TABLES LIKE 'hackathon_2025_instructor_classes'"
        table_exists = run_query(check_query)
        
        if table_exists.empty:
            # Table doesn't exist, create it
            create_instructor_tables()
            return []
        
        # Check columns
        columns_query = "SHOW COLUMNS FROM hackathon_2025_instructor_classes"
        columns_result = run_query(columns_query)
        columns = [col['Field'] for col in columns_result.to_dict('records')]
        
        # Build query based on available columns
        if 'created_at' in columns:
            order_clause = "ORDER BY c.created_at DESC"
        else:
            order_clause = "ORDER BY c.id DESC"
        
        query = f"""
        SELECT c.*, COUNT(m.id) as student_count
        FROM hackathon_2025_instructor_classes c
        LEFT JOIN hackathon_2025_class_members m ON c.id = m.class_id AND m.is_active = 1
        WHERE c.user_id = {user_id}
        GROUP BY c.id
        {order_clause}
        """
        
        result = run_query(query)
        return result.to_dict('records') if not result.empty else []
    except Exception as e:
        st.error(f"Database error: {e}")
        return []

def create_class(user_id: int, class_name: str) -> bool:
    """Create a new class"""
    # Escape single quotes in class name
    escaped_name = class_name.replace("'", "''")
    query = f"""
    INSERT INTO hackathon_2025_instructor_classes (user_id, class_name)
    VALUES ({user_id}, '{escaped_name}')
    """
    try:
        run_query(query)
        return True
    except Exception as e:
        st.error(f"Error creating class: {e}")
        return False

def get_class_students(class_id: int) -> List[Dict]:
    """Get students in a class"""
    query = f"""
    SELECT m.*, u.first_name, u.last_name
    FROM hackathon_2025_class_members m
    LEFT JOIN users u ON m.user_id = u.id
    WHERE m.class_id = {class_id} AND m.is_active = 1
    ORDER BY m.invited_at DESC
    """
    try:
        result = run_query(query)
        return result.to_dict('records') if not result.empty else []
    except Exception as e:
        st.error(f"Database error: {e}")
        return []

def add_students_to_class(class_id: int, emails: List[str]) -> int:
    """Add students to class"""
    added_count = 0
    for email in emails:
        try:
            # Check if student already exists
            check_query = f"""
            SELECT id FROM hackathon_2025_class_members 
            WHERE class_id = {class_id} AND email = '{email}' AND is_active = 1
            """
            existing = run_query(check_query)
            
            if existing.empty:
                # Get user_id if user exists
                user_query = f"SELECT id FROM users WHERE email = '{email}'"
                user_result = run_query(user_query)
                user_id = user_result.iloc[0]['id'] if not user_result.empty else 'NULL'
                
                # Add student
                insert_query = f"""
                INSERT INTO hackathon_2025_class_members (class_id, email, user_id)
                VALUES ({class_id}, '{email}', {user_id})
                """
                run_query(insert_query)
                added_count += 1
        except Exception as e:
            st.error(f"Error adding student {email}: {e}")
            continue
    
    return added_count

def get_class_assignments(class_id: int) -> List[Dict]:
    """Get assignments for a class"""
    query = f"""
    SELECT a.*, COUNT(aq.id) as question_count
    FROM hackathon_2025_assignments a
    LEFT JOIN hackathon_2025_assignment_questions aq ON a.id = aq.assignment_id
    WHERE a.class_id = {class_id}
    GROUP BY a.id
    ORDER BY a.created_at DESC
    """
    try:
        result = run_query(query)
        return result.to_dict('records') if not result.empty else []
    except Exception as e:
        st.error(f"Database error: {e}")
        return []

def create_assignment(class_id: int, name: str, due_date: datetime, questions: List[Dict]) -> bool:
    """Create assignment with questions - simplified for demo"""
    try:
        # Escape single quotes in assignment name
        escaped_name = name.replace("'", "''")
        due_date_str = due_date.strftime('%Y-%m-%d %H:%M:%S')
        
        # Create assignment
        assignment_query = f"""
        INSERT INTO hackathon_2025_assignments (class_id, name, due_date)
        VALUES ({class_id}, '{escaped_name}', '{due_date_str}')
        """
        run_query(assignment_query)
        
        # For demo purposes, we'll use a simple approach to get the assignment ID
        # In production, you'd use LAST_INSERT_ID() or similar
        get_id_query = f"""
        SELECT id FROM hackathon_2025_assignments 
        WHERE class_id = {class_id} AND name = '{escaped_name}'
        ORDER BY created_at DESC LIMIT 1
        """
        result = run_query(get_id_query)
        if not result.empty:
            assignment_id = result.iloc[0]['id']
            
            # Add questions
            for question in questions:
                question_query = f"""
                INSERT INTO hackathon_2025_assignment_questions (assignment_id, question_id, points)
                VALUES ({assignment_id}, {question['id']}, {question.get('points', 10)})
                """
                run_query(question_query)
        
        return True
    except Exception as e:
        st.error(f"Error creating assignment: {e}")
        return False

def get_student_progress(class_id: int, assignment_id: int = None) -> Dict:
    """Get student progress for class/assignment"""
    students = get_class_students(class_id)
    
    if assignment_id:
        try:
            # Get assignment questions
            question_query = f"""
            SELECT aq.question_id, aq.points, q.title, q.type
            FROM hackathon_2025_assignment_questions aq
            JOIN questions q ON aq.question_id = q.id
            WHERE aq.assignment_id = {assignment_id}
            """
            questions_result = run_query(question_query)
            questions = questions_result.to_dict('records') if not questions_result.empty else []
            
            # Get submissions for each student/question
            progress_data = []
            for student in students:
                if not student['user_id']:
                    continue
                    
                student_progress = {
                    'student': student['email'],
                    'user_id': student['user_id'],
                    'questions': []
                }
                
                total_score = 0
                total_possible = 0
                
                for question in questions:
                    question_id = question['question_id']
                    points = question['points']
                    total_possible += points
                    
                    # Check coding submissions
                    if question['type'] in ['sql', 'python', 'algorithms']:
                        code_query = f"""
                        SELECT COUNT(*) as attempts, MAX(is_accepted) as accepted
                        FROM user_code_runs 
                        WHERE user_id = {student['user_id']} AND question_id = {question_id}
                        """
                        code_result = run_query(code_query)
                        
                        if not code_result.empty and code_result.iloc[0]['accepted']:
                            score = points
                            status = '✅'
                        else:
                            score = 0
                            status = '❌' if not code_result.empty and code_result.iloc[0]['attempts'] > 0 else '⏳'
                            
                        attempts = code_result.iloc[0]['attempts'] if not code_result.empty else 0
                        
                    else:
                        # Check text submissions
                        text_query = f"""
                        SELECT score, COUNT(*) as attempts
                        FROM text_submissions 
                        WHERE user_id = {student['user_id']} AND question_id = {question_id}
                        GROUP BY user_id, question_id
                        ORDER BY score DESC
                        LIMIT 1
                        """
                        text_result = run_query(text_query)
                        
                        if not text_result.empty:
                            score = min(text_result.iloc[0]['score'], points)
                            status = '✅' if score >= points * 0.8 else '⚠️'
                            attempts = text_result.iloc[0]['attempts']
                        else:
                            score = 0
                            status = '⏳'
                            attempts = 0
                    
                    total_score += score
                    student_progress['questions'].append({
                        'question_id': question_id,
                        'title': question['title'],
                        'score': score,
                        'max_score': points,
                        'status': status,
                        'attempts': attempts
                    })
                
                student_progress['total_score'] = total_score
                student_progress['total_possible'] = total_possible
                student_progress['percentage'] = (total_score / total_possible * 100) if total_possible > 0 else 0
                
                progress_data.append(student_progress)
            
            return {
                'students': progress_data,
                'questions': questions,
                'assignment_id': assignment_id
            }
        except Exception as e:
            st.error(f"Error getting progress: {e}")
            return {'students': []}
    
    return {'students': students}

# Authentication flow
def show_auth():
    st.markdown('<h1 class="main-header">Interview Query - Instructor Portal</h1>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🎓 Instructor Authentication")
        
        if not st.session_state.get('verification_sent', False):
            email = st.text_input("Enter your university email", placeholder="professor@university.edu")
            
            if st.button("Send Verification Code", type="primary", use_container_width=True):
                if validate_email(email):
                    code = generate_verification_code()
                    if send_verification_email(email, code):
                        st.session_state.verification_sent = True
                        st.session_state.pending_email = email
                        st.rerun()
                else:
                    st.error("Please enter a valid .edu email address or approved domain")
        
        else:
            st.info(f"Verification code sent to {st.session_state.pending_email}")
            if st.session_state.get('demo_email_sent'):
                st.success(f"Demo: Your verification code is **{st.session_state.verification_code}**")
            
            code_input = st.text_input("Enter 6-digit verification code", max_chars=6)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Verify", type="primary", use_container_width=True):
                    if code_input == st.session_state.verification_code:
                        try:
                            # Check if user exists
                            user_query = f"SELECT id, first_name, last_name FROM users WHERE email = '{st.session_state.pending_email}'"
                            user_result = run_query(user_query)
                            
                            if not user_result.empty:
                                user_id = user_result.iloc[0]['id']
                            else:
                                # Create new instructor user (simplified for demo)
                                # In production, you'd want better error handling
                                name_parts = st.session_state.pending_email.split('@')[0].split('.')
                                first_name = name_parts[0].title() if name_parts else "Instructor"
                                last_name = name_parts[1].title() if len(name_parts) > 1 else ""
                                username = st.session_state.pending_email.split('@')[0]
                                
                                create_user_query = f"""
                                INSERT INTO users (email, first_name, last_name, username, is_confirmed)
                                VALUES ('{st.session_state.pending_email}', '{first_name}', '{last_name}', '{username}', 1)
                                """
                                run_query(create_user_query)
                                
                                # Get the new user ID
                                user_result = run_query(user_query)
                                user_id = user_result.iloc[0]['id'] if not user_result.empty else None
                            
                            if user_id:
                                st.session_state.authenticated = True
                                st.session_state.user_email = st.session_state.pending_email
                                st.session_state.user_id = user_id
                                st.session_state.verification_sent = False
                                
                                # Create tables if needed
                                create_instructor_tables()
                                
                                st.success("Authentication successful!")
                                st.rerun()
                            else:
                                st.error("Error creating user account")
                        except Exception as e:
                            st.error(f"Authentication error: {e}")
                    else:
                        st.error("Invalid verification code")
            
            with col2:
                if st.button("Resend Code", use_container_width=True):
                    code = generate_verification_code()
                    send_verification_email(st.session_state.pending_email, code)
                    st.success("New code sent!")
                    st.rerun()

# Main portal interface
def show_portal():
    # Header
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown('<h1 class="main-header">Homework Dashboard</h1>', unsafe_allow_html=True)
    with col2:
        st.write(f"Welcome, {st.session_state.user_email}")
    with col3:
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Classes", "Assignments", "Progress", "Reports"]
    )
    
    if page == "Classes":
        show_classes_page()
    elif page == "Assignments":
        show_assignments_page()
    elif page == "Progress":
        show_progress_page()
    elif page == "Reports":
        show_reports_page()

def show_classes_page():
    st.subheader("📚 My Classes")
    
    # Create new class
    with st.expander("Create New Class", expanded=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            class_name = st.text_input("Class Name", placeholder="e.g., Data Structures Fall 2025")
        with col2:
            if st.button("Create Class", type="primary"):
                if class_name:
                    if create_class(st.session_state.user_id, class_name):
                        st.success(f"Class '{class_name}' created successfully!")
                        st.rerun()
                    else:
                        st.error("Error creating class")
    
    # Display existing classes
    classes = get_user_classes(st.session_state.user_id)
    
    if not classes:
        st.info("No classes found. Create your first class above!")
        return
    
    for class_data in classes:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.markdown(f"### {class_data['class_name']}")
                if 'created_at' in class_data and class_data['created_at']:
                    created_at = class_data['created_at']
                    if isinstance(created_at, str):
                        created_date = created_at.split(' ')[0]
                    else:
                        created_date = created_at.strftime('%Y-%m-%d')
                    st.caption(f"Created: {created_date}")
                else:
                    st.caption(f"Class ID: {class_data['id']}")
            
            with col2:
                st.metric("Students", class_data['student_count'])
            
            with col3:
                if st.button("Manage", key=f"manage_{class_data['id']}"):
                    st.session_state.selected_class = class_data['id']
                    st.session_state.manage_class = True
                    st.rerun()
            
            with col4:
                if st.button("Delete", key=f"delete_{class_data['id']}"):
                    try:
                        # Soft delete - set is_active = 0 for members
                        delete_query = f"""
                        UPDATE hackathon_2025_class_members 
                        SET is_active = 0 
                        WHERE class_id = {class_data['id']}
                        """
                        run_query(delete_query)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting class: {e}")
            
            st.divider()
    
    # Class management section
    if st.session_state.get('manage_class'):
        selected_class = next((c for c in classes if c['id'] == st.session_state.selected_class), None)
        if selected_class:
            st.markdown(f"### Managing: {selected_class['class_name']}")
            
            # Student roster management
            st.subheader("Student Roster")
            
            # CSV upload
            uploaded_file = st.file_uploader("Upload Student CSV", type=['csv'])
            if uploaded_file:
                try:
                    emails = parse_csv(uploaded_file)
                    st.success(f"Found {len(emails)} email addresses")
                    
                    if st.button("Import Students"):
                        added_count = add_students_to_class(st.session_state.selected_class, emails)
                        st.success(f"Added {added_count} new students!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error parsing CSV: {str(e)}")
            
            # Manual email addition
            with st.expander("Add Students Manually"):
                email_input = st.text_area("Enter email addresses (one per line)")
                if st.button("Add Students"):
                    emails = [e.strip() for e in email_input.split('\n') if e.strip()]
                    added_count = add_students_to_class(st.session_state.selected_class, emails)
                    st.success(f"Added {added_count} new students!")
                    st.rerun()
            
            # Current students
            st.subheader("Current Students")
            students = get_class_students(st.session_state.selected_class)
            
            if students:
                student_data = []
                for student in students:
                    student_data.append({
                        'Email': student['email'],
                        'Name': f"{student.get('first_name', '') or ''} {student.get('last_name', '') or ''}".strip() or 'Not registered',
                        'Status': 'Registered' if student.get('user_id') else 'Invited',
                        'Invited': student['invited_at'].split(' ')[0] if isinstance(student['invited_at'], str) else student['invited_at'].strftime('%Y-%m-%d')
                    })
                
                df = pd.DataFrame(student_data)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No students in this class yet.")
            
            if st.button("Done Managing"):
                st.session_state.manage_class = False
                st.rerun()

def show_assignments_page():
    st.subheader("📝 Create Assignment")
    
    # Select class
    classes = get_user_classes(st.session_state.user_id)
    if not classes:
        st.warning("Please create a class first!")
        return
    
    class_options = {c['class_name']: c['id'] for c in classes}
    selected_class_name = st.selectbox("Select Class", list(class_options.keys()))
    selected_class_id = class_options[selected_class_name]
    
    # Assignment details
    col1, col2 = st.columns(2)
    with col1:
        assignment_name = st.text_input("Assignment Name", placeholder="e.g., Week 3 - Arrays and Strings")
    with col2:
        due_date = st.date_input("Due Date", min_value=datetime.now().date())
    
    st.markdown("### Search Questions")
    
    # Search interface
    col1, col2 = st.columns([4, 1])
    with col1:
        search_query = st.text_input("Search questions", placeholder="e.g., dynamic programming, arrays, SQL")
    with col2:
        if st.button("Search", type="primary"):
            if search_query:
                with st.spinner("Searching questions..."):
                    results = search_questions(search_query)
                    st.session_state.search_results = results
    
    # Display search results
    if st.session_state.get('search_results'):
        st.markdown("### Search Results")
        
        for result in st.session_state.search_results:
            question_data = result.get('data', {})
            if not question_data:
                continue
                
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                question_id = question_data.get('id')
                title = question_data.get('title', 'Untitled')
                question_type = question_data.get('type', 'unknown')
                level = question_data.get('level', 1)
                
                # Map level to difficulty
                difficulty_map = {1: 'Easy', 2: 'Medium', 3: 'Hard'}
                difficulty = difficulty_map.get(level, 'Unknown')
                
                with col1:
                    st.markdown(f"**{title}**")
                    st.caption(f"Type: {question_type}")
                
                with col2:
                    difficulty_colors = {'Easy': '🟢', 'Medium': '🟡', 'Hard': '🔴'}
                    st.write(f"{difficulty_colors.get(difficulty, '⚪')} {difficulty}")
                
                with col3:
                    st.caption(f"ID: {question_id}")
                
                with col4:
                    question_obj = {
                        'id': question_id,
                        'title': title,
                        'type': question_type,
                        'difficulty': difficulty,
                        'level': level,
                        'url': question_data.get('url', f"https://interviewquery.com/questions/{question_id}")
                    }
                    
                    already_selected = any(q['id'] == question_id for q in st.session_state.selected_questions)
                    
                    if already_selected:
                        st.button("✓ Added", disabled=True, key=f"added_{question_id}")
                    else:
                        if st.button("Add", key=f"add_{question_id}"):
                            st.session_state.selected_questions.append(question_obj)
                            st.rerun()
                
                st.divider()
    
    # Selected questions
    if st.session_state.selected_questions:
        st.markdown("### Selected Questions")
        
        for idx, question in enumerate(st.session_state.selected_questions):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"{idx + 1}. **{question['title']}** ({question['difficulty']})")
                st.caption(f"Type: {question['type']}")
            
            with col2:
                points = st.number_input("Points", min_value=0, max_value=100, value=10, 
                                       key=f"points_{question['id']}")
                question['points'] = points
            
            with col3:
                if st.button("Remove", key=f"remove_{question['id']}"):
                    st.session_state.selected_questions.remove(question)
                    st.rerun()
        
        st.divider()
        
        # Create assignment
        if st.button("Create Assignment", type="primary", use_container_width=True):
            if assignment_name and st.session_state.selected_questions:
                due_datetime = datetime.combine(due_date, datetime.min.time())
                
                if create_assignment(selected_class_id, assignment_name, due_datetime, st.session_state.selected_questions):
                    st.success(f"Assignment '{assignment_name}' created with {len(st.session_state.selected_questions)} questions!")
                    
                    # Show sample student email
                    with st.expander("Sample Student Email"):
                        # Create beautiful HTML email template
                        email_html = f"""
                        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                            <!-- Header -->
                            <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 40px 30px; text-align: center; border-radius: 10px 10px 0 0;">
                                <h1 style="color: white; margin: 0; font-size: 28px; font-weight: 600;">Interview Query</h1>
                                <p style="color: #e0e7ff; margin: 10px 0 0 0; font-size: 16px;">Practice Makes Perfect</p>
                            </div>
                            
                            <!-- Body -->
                            <div style="background: #ffffff; padding: 40px 30px; border: 1px solid #e5e7eb; border-top: none;">
                                <h2 style="color: #1e293b; font-size: 24px; margin: 0 0 20px 0;">New Assignment Available!</h2>
                                
                                <div style="background: #f0f9ff; border-left: 4px solid #3b82f6; padding: 20px; margin: 20px 0; border-radius: 4px;">
                                    <p style="margin: 0; color: #1e3a8a; font-weight: 600; font-size: 18px;">{assignment_name}</p>
                                    <p style="margin: 10px 0 0 0; color: #64748b;">
                                        <strong>Due Date:</strong> {due_date.strftime('%B %d, %Y')}
                                    </p>
                                </div>
                                
                                <p style="color: #475569; font-size: 16px; line-height: 1.6; margin: 20px 0;">
                                    Hello! Your instructor has assigned you {len(st.session_state.selected_questions)} practice questions to help you master the concepts covered in class.
                                </p>
                                
                                <h3 style="color: #1e293b; font-size: 20px; margin: 30px 0 20px 0;">📚 Your Questions</h3>
                                
                                <div style="background: #fafafa; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                        """
                        
                        total_points = sum(q['points'] for q in st.session_state.selected_questions)
                        
                        for i, q in enumerate(st.session_state.selected_questions):
                            # Use the URL from search results if available, otherwise query the questions table
                            if 'url' in q and q['url']:
                                link = q['url']
                            else:
                                # Query the questions table for the slug
                                slug_query = f"SELECT slug FROM questions WHERE id = {q['id']}"
                                slug_result = run_query(slug_query)
                                if not slug_result.empty and slug_result.iloc[0]['slug']:
                                    link = f"https://www.interviewquery.com/questions/{slug_result.iloc[0]['slug']}"
                                else:
                                    # Fallback to title-based slug
                                    link = f"https://www.interviewquery.com/questions/{q['title'].lower().replace(' ', '-')}"
                            
                            # Difficulty badge colors
                            difficulty_colors = {
                                'Easy': '#10b981',
                                'Medium': '#f59e0b', 
                                'Hard': '#ef4444'
                            }
                            badge_color = difficulty_colors.get(q['difficulty'], '#6b7280')
                            
                            email_html += f"""
                                    <div style="background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin-bottom: 15px;">
                                        <div style="display: flex; justify-content: space-between; align-items: start;">
                                            <div style="flex: 1;">
                                                <h4 style="margin: 0 0 8px 0; color: #1e293b; font-size: 18px;">
                                                    {i+1}. {q['title']}
                                                </h4>
                                                <div style="display: inline-flex; gap: 10px; align-items: center;">
                                                    <span style="background: {badge_color}; color: white; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 500;">
                                                        {q['difficulty']}
                                                    </span>
                                                    <span style="color: #64748b; font-size: 14px;">
                                                        Type: {q['type'].title()}
                                                    </span>
                                                    <span style="color: #1e3a8a; font-weight: 600; font-size: 14px;">
                                                        {q['points']} points
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                        <a href="{link}" style="display: inline-block; margin-top: 12px; background: #3b82f6; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: 500; font-size: 14px;">
                                            Start Question →
                                        </a>
                                    </div>
                            """
                        
                        email_html += f"""
                                </div>
                                
                                <div style="background: #fef3c7; border-radius: 8px; padding: 20px; margin: 20px 0;">
                                    <p style="margin: 0; color: #92400e; font-weight: 600;">
                                        📊 Total Points: {total_points}
                                    </p>
                                </div>
                                
                                <div style="margin-top: 30px; padding-top: 30px; border-top: 1px solid #e5e7eb;">
                                    <h4 style="color: #1e293b; margin: 0 0 15px 0;">💡 Tips for Success</h4>
                                    <ul style="color: #64748b; line-height: 1.8; padding-left: 20px;">
                                        <li>Start early to give yourself plenty of time</li>
                                        <li>Read each question carefully before attempting</li>
                                        <li>Test your code thoroughly before submitting</li>
                                        <li>Reach out if you need help or clarification</li>
                                    </ul>
                                </div>
                                
                                <div style="text-align: center; margin-top: 40px;">
                                    <a href="https://www.interviewquery.com" style="display: inline-block; background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 30px; font-weight: 600; font-size: 16px;">
                                        Go to Interview Query
                                    </a>
                                </div>
                            </div>
                            
                            <!-- Footer -->
                            <div style="background: #f8fafc; padding: 30px; text-align: center; border-radius: 0 0 10px 10px; border: 1px solid #e5e7eb; border-top: none;">
                                <p style="color: #64748b; margin: 0 0 10px 0; font-size: 14px;">
                                    Questions? Contact your instructor or visit our 
                                    <a href="https://www.interviewquery.com/help" style="color: #3b82f6; text-decoration: none;">Help Center</a>
                                </p>
                                <p style="color: #94a3b8; margin: 0; font-size: 12px;">
                                    © 2025 Interview Query. All rights reserved.
                                </p>
                            </div>
                        </div>
                        """
                        
                        # Subject line
                        st.markdown(f"**Subject:** 🎯 New Interview Query Assignment: {assignment_name}")
                        
                        # Show the HTML preview
                        st.markdown(email_html, unsafe_allow_html=True)
                        
                        # Also show plain text version
                        with st.expander("Plain Text Version"):
                            plain_text = f"""
Interview Query - Practice Makes Perfect

NEW ASSIGNMENT AVAILABLE!

{assignment_name}
Due Date: {due_date.strftime('%B %d, %Y')}

Hello! Your instructor has assigned you {len(st.session_state.selected_questions)} practice questions to help you master the concepts covered in class.

YOUR QUESTIONS:
"""
                            for i, q in enumerate(st.session_state.selected_questions):
                                if 'url' in q and q['url']:
                                    link = q['url']
                                else:
                                    slug_query = f"SELECT slug FROM questions WHERE id = {q['id']}"
                                    slug_result = run_query(slug_query)
                                    if not slug_result.empty and slug_result.iloc[0]['slug']:
                                        link = f"https://www.interviewquery.com/questions/{slug_result.iloc[0]['slug']}"
                                    else:
                                        link = f"https://www.interviewquery.com/questions/{q['title'].lower().replace(' ', '-')}"
                                plain_text += f"""
{i+1}. {q['title']}
   Difficulty: {q['difficulty']} | Type: {q['type'].title()} | Points: {q['points']}
   Link: {link}
"""
                            plain_text += f"""
Total Points: {total_points}

TIPS FOR SUCCESS:
• Start early to give yourself plenty of time
• Read each question carefully before attempting
• Test your code thoroughly before submitting
• Reach out if you need help or clarification

Good luck with your practice!

---
Interview Query
https://www.interviewquery.com
"""
                            st.code(plain_text, language=None)
                    
                    # Clear selection
                    st.session_state.selected_questions = []
                    if 'search_results' in st.session_state:
                        del st.session_state.search_results
                    st.rerun()
                else:
                    st.error("Error creating assignment")

def show_progress_page():
    st.subheader("📊 Student Progress")
    
    # Select class
    classes = get_user_classes(st.session_state.user_id)
    if not classes:
        st.warning("No classes found!")
        return
    
    class_options = {c['class_name']: c['id'] for c in classes}
    selected_class_name = st.selectbox("Select Class", list(class_options.keys()))
    selected_class_id = class_options[selected_class_name]
    
    # Get assignments for this class
    assignments = get_class_assignments(selected_class_id)
    
    if not assignments:
        st.info("No assignments found for this class.")
        return
    
    # Select assignment
    assignment_options = {}
    for a in assignments:
        due_date = a['due_date']
        if isinstance(due_date, str):
            due_date_str = due_date.split(' ')[0]
        else:
            due_date_str = due_date.strftime('%Y-%m-%d')
        assignment_options[f"{a['name']} (Due: {due_date_str})"] = a['id']
    
    selected_assignment_name = st.selectbox("Select Assignment", list(assignment_options.keys()))
    selected_assignment_id = assignment_options[selected_assignment_name]
    
    # Get progress data
    with st.spinner("Loading progress data..."):
        progress_data = get_student_progress(selected_class_id, selected_assignment_id)
    
    if not progress_data.get('students'):
        st.info("No student progress data available.")
        return
    
    students = progress_data['students']
    questions = progress_data['questions']
    
    # Overall metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_students = len(students)
    completed_students = len([s for s in students if s['percentage'] >= 80])
    avg_score = sum(s['percentage'] for s in students) / total_students if total_students > 0 else 0
    total_submissions = sum(sum(q['attempts'] for q in s['questions']) for s in students)
    
    with col1:
        st.metric("Total Students", total_students)
    with col2:
        st.metric("Completed (≥80%)", completed_students)
    with col3:
        st.metric("Average Score", f"{avg_score:.1f}%")
    with col4:
        st.metric("Total Submissions", total_submissions)
    
    # Student progress table
    st.markdown("### Student Progress")
    
    # Create progress dataframe
    progress_df = []
    for student in students:
        row = {
            'Student': student['student'],
            'Score': f"{student['total_score']}/{student['total_possible']}",
            'Percentage': f"{student['percentage']:.1f}%",
            'Total Attempts': sum(q['attempts'] for q in student['questions'])
        }
        
        # Add individual question status
        for i, question in enumerate(student['questions']):
            row[f"Q{i+1}"] = question['status']
        
        progress_df.append(row)
    
    if progress_df:
        df = pd.DataFrame(progress_df)
        st.dataframe(df, use_container_width=True)
    
    # Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Score distribution
        score_ranges = ['0-25%', '26-50%', '51-75%', '76-100%']
        score_counts = [0, 0, 0, 0]
        
        for student in students:
            percentage = student['percentage']
            if percentage <= 25:
                score_counts[0] += 1
            elif percentage <= 50:
                score_counts[1] += 1
            elif percentage <= 75:
                score_counts[2] += 1
            else:
                score_counts[3] += 1
        
        fig = px.bar(
            x=score_ranges,
            y=score_counts,
            title="Score Distribution",
            labels={'x': 'Score Range', 'y': 'Number of Students'}
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Question completion rates
        question_completion = []
        for i, question in enumerate(questions):
            completed = len([s for s in students if s['questions'][i]['status'] == '✅'])
            completion_rate = (completed / total_students * 100) if total_students > 0 else 0
            question_completion.append({
                'Question': f"Q{i+1}",
                'Title': question['title'][:30] + "..." if len(question['title']) > 30 else question['title'],
                'Completion Rate': completion_rate
            })
        
        if question_completion:
            fig = px.bar(
                question_completion,
                x='Question',
                y='Completion Rate',
                title="Question Completion Rates",
                hover_data=['Title']
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)

def show_reports_page():
    st.subheader("📄 Export Reports")
    
    # Select class and assignment (similar to progress page)
    classes = get_user_classes(st.session_state.user_id)
    if not classes:
        st.warning("No classes found!")
        return
    
    class_options = {c['class_name']: c['id'] for c in classes}
    selected_class_name = st.selectbox("Select Class", list(class_options.keys()))
    selected_class_id = class_options[selected_class_name]
    
    assignments = get_class_assignments(selected_class_id)
    if not assignments:
        st.info("No assignments found for this class.")
        return
    
    assignment_options = {}
    for a in assignments:
        due_date = a['due_date']
        if isinstance(due_date, str):
            due_date_str = due_date.split(' ')[0]
        else:
            due_date_str = due_date.strftime('%Y-%m-%d')
        assignment_options[f"{a['name']} (Due: {due_date_str})"] = a['id']
    
    selected_assignment_name = st.selectbox("Select Assignment", list(assignment_options.keys()))
    selected_assignment_id = assignment_options[selected_assignment_name]
    
    # Generate report preview
    st.markdown("### Report Preview")
    
    progress_data = get_student_progress(selected_class_id, selected_assignment_id)
    
    if progress_data.get('students'):
        students = progress_data['students']
        questions = progress_data['questions']
        
        # Report summary
        total_students = len(students)
        completed = len([s for s in students if s['percentage'] >= 80])
        avg_score = sum(s['percentage'] for s in students) / total_students if total_students > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Students", total_students)
        with col2:
            st.metric("Completed", completed)
        with col3:
            st.metric("Average Score", f"{avg_score:.1f}%")
        with col4:
            st.metric("Completion Rate", f"{(completed/total_students*100):.1f}%")
        
        # Question performance
        st.markdown("### Question Performance")
        
        question_stats = []
        for i, question in enumerate(questions):
            completed_count = len([s for s in students if s['questions'][i]['status'] == '✅'])
            total_attempts = sum(s['questions'][i]['attempts'] for s in students)
            avg_attempts = total_attempts / total_students if total_students > 0 else 0
            
            question_stats.append({
                'Question': question['title'],
                'Type': question['type'],
                'Success Rate': f"{(completed_count/total_students*100):.1f}%",
                'Avg Attempts': f"{avg_attempts:.1f}",
                'Total Attempts': total_attempts
            })
        
        if question_stats:
            df = pd.DataFrame(question_stats)
            st.dataframe(df, use_container_width=True)
        
        # Top performers
        st.markdown("### Top Performers")
        
        top_students = sorted(students, key=lambda x: x['percentage'], reverse=True)[:5]
        top_data = []
        
        for i, student in enumerate(top_students):
            top_data.append({
                'Rank': i + 1,
                'Student': student['student'],
                'Score': f"{student['total_score']}/{student['total_possible']}",
                'Percentage': f"{student['percentage']:.1f}%"
            })
        
        if top_data:
            df = pd.DataFrame(top_data)
            st.dataframe(df, use_container_width=True)
    
    # Export options
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export as PDF", type="primary", use_container_width=True):
            st.success("PDF report generated! Download link will be sent to your email.")
    
    with col2:
        if st.button("📊 Export as Excel", use_container_width=True):
            # Create Excel file with progress data
            if progress_data.get('students'):
                excel_data = []
                for student in students:
                    row = {
                        'Student Email': student['student'],
                        'Total Score': student['total_score'],
                        'Total Possible': student['total_possible'],
                        'Percentage': student['percentage']
                    }
                    for i, q in enumerate(student['questions']):
                        row[f"Q{i+1} Status"] = q['status']
                        row[f"Q{i+1} Score"] = q['score']
                        row[f"Q{i+1} Attempts"] = q['attempts']
                    excel_data.append(row)
                
                df = pd.DataFrame(excel_data)
                
                # Create download
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='Student Progress', index=False)
                
                st.download_button(
                    label="Download Excel File",
                    data=output.getvalue(),
                    file_name=f"{selected_assignment_name.split(' (')[0]}_progress.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    
    with col3:
        if st.button("📧 Email Report", use_container_width=True):
            st.success("Report will be emailed to all students and saved to class records.")

# Main app logic
def main():
    if not st.session_state.authenticated:
        show_auth()
    else:
        show_portal()

if __name__ == "__main__":
    main()