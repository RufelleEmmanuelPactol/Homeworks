import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import hashlib
import secrets
import json
from io import BytesIO
import re
from typing import List, Dict, Optional
import requests

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
    .student-row {
        padding: 0.5rem;
        border-bottom: 1px solid #e5e7eb;
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

# Mock data for demonstration
WHITELISTED_DOMAINS = ['.edu', '@interviewquery.com']
MOCK_USERS = {
    'professor@university.edu': {'id': 1, 'name': 'Dr. Smith'},
    'instructor@college.edu': {'id': 2, 'name': 'Prof. Johnson'},
    'demo@interviewquery.com': {'id': 3, 'name': 'Demo User'}
}

# Mock classes data
MOCK_CLASSES = [
    {'id': 1, 'name': 'Data Structures Fall 2025', 'students': 25, 'created': '2025-01-10'},
    {'id': 2, 'name': 'Algorithms Spring 2025', 'students': 30, 'created': '2025-01-12'}
]

# Mock questions from IQ platform
MOCK_QUESTIONS = [
    {'id': 101, 'title': 'Two Sum', 'difficulty': 'Easy', 'category': 'Arrays', 'completion_rate': 85},
    {'id': 102, 'title': 'Binary Search Tree', 'difficulty': 'Medium', 'category': 'Trees', 'completion_rate': 65},
    {'id': 103, 'title': 'Dynamic Programming - Knapsack', 'difficulty': 'Hard', 'category': 'DP', 'completion_rate': 45},
    {'id': 104, 'title': 'SQL Joins', 'difficulty': 'Medium', 'category': 'SQL', 'completion_rate': 70},
    {'id': 105, 'title': 'Merge K Sorted Lists', 'difficulty': 'Hard', 'category': 'Heaps', 'completion_rate': 40},
    {'id': 106, 'title': 'Graph Traversal', 'difficulty': 'Medium', 'category': 'Graphs', 'completion_rate': 60},
    {'id': 107, 'title': 'String Manipulation', 'difficulty': 'Easy', 'category': 'Strings', 'completion_rate': 90},
    {'id': 108, 'title': 'Sliding Window', 'difficulty': 'Medium', 'category': 'Arrays', 'completion_rate': 55}
]

# Helper functions
def validate_email(email: str) -> bool:
    """Validate if email is from whitelisted domain"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False
    
    return any(email.endswith(domain) for domain in WHITELISTED_DOMAINS)

def generate_verification_code() -> str:
    """Generate 6-digit verification code"""
    return f"{secrets.randbelow(1000000):06d}"

def send_verification_email(email: str, code: str):
    """Mock email sending"""
    st.session_state.verification_code = code
    return True

def create_signed_link(question_id: int, assignment_id: int, user_email: str) -> str:
    """Create signed link for question access"""
    timestamp = int(datetime.now().timestamp())
    data = f"{question_id}:{assignment_id}:{user_email}:{timestamp}"
    signature = hashlib.sha256(data.encode()).hexdigest()[:16]
    return f"https://interviewquery.com/questions/{question_id}?hw={assignment_id}&u={signature}"

def parse_csv(file) -> List[str]:
    """Parse CSV file and extract emails"""
    df = pd.read_csv(file)
    # Try to find email column
    email_columns = [col for col in df.columns if 'email' in col.lower()]
    if email_columns:
        return df[email_columns[0]].dropna().tolist()
    # If no email column, assume first column
    return df.iloc[:, 0].dropna().tolist()

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
                    st.error("Please enter a valid .edu email address")
        
        else:
            st.info(f"Verification code sent to {st.session_state.pending_email}")
            st.caption(f"Demo: Your code is {st.session_state.verification_code}")
            
            code_input = st.text_input("Enter 6-digit verification code", max_chars=6)
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("Verify", type="primary", use_container_width=True):
                    if code_input == st.session_state.verification_code:
                        st.session_state.authenticated = True
                        st.session_state.user_email = st.session_state.pending_email
                        st.session_state.user_id = MOCK_USERS.get(st.session_state.pending_email, {}).get('id', 1)
                        st.session_state.verification_sent = False
                        st.success("Authentication successful!")
                        st.rerun()
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
                    # Mock creating class
                    new_class = {
                        'id': len(MOCK_CLASSES) + 1,
                        'name': class_name,
                        'students': 0,
                        'created': datetime.now().strftime('%Y-%m-%d')
                    }
                    MOCK_CLASSES.append(new_class)
                    st.success(f"Class '{class_name}' created successfully!")
                    st.rerun()
    
    # Display existing classes
    for class_data in MOCK_CLASSES:
        with st.container():
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                st.markdown(f"### {class_data['name']}")
                st.caption(f"Created: {class_data['created']}")
            
            with col2:
                st.metric("Students", class_data['students'])
            
            with col3:
                if st.button("Manage", key=f"manage_{class_data['id']}"):
                    st.session_state.selected_class = class_data['id']
                    st.session_state.manage_class = True
                    st.rerun()
            
            with col4:
                if st.button("Delete", key=f"delete_{class_data['id']}"):
                    MOCK_CLASSES.remove(class_data)
                    st.rerun()
            
            st.divider()
    
    # Class management section
    if st.session_state.get('manage_class'):
        selected_class = next((c for c in MOCK_CLASSES if c['id'] == st.session_state.selected_class), None)
        if selected_class:
            st.markdown(f"### Managing: {selected_class['name']}")
            
            # Student roster management
            st.subheader("Student Roster")
            
            # CSV upload
            uploaded_file = st.file_uploader("Upload Student CSV", type=['csv'])
            if uploaded_file:
                try:
                    emails = parse_csv(uploaded_file)
                    st.success(f"Found {len(emails)} email addresses")
                    
                    if st.button("Import Students"):
                        selected_class['students'] += len(emails)
                        st.success(f"Imported {len(emails)} students!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error parsing CSV: {str(e)}")
            
            # Manual email addition
            with st.expander("Add Students Manually"):
                email_input = st.text_area("Enter email addresses (one per line)")
                if st.button("Add Students"):
                    emails = [e.strip() for e in email_input.split('\n') if e.strip()]
                    selected_class['students'] += len(emails)
                    st.success(f"Added {len(emails)} students!")
                    st.rerun()
            
            # Mock student list
            st.subheader("Current Students")
            mock_students = [
                {'email': 'student1@university.edu', 'status': 'Active', 'assignments_completed': 3},
                {'email': 'student2@university.edu', 'status': 'Active', 'assignments_completed': 2},
                {'email': 'student3@university.edu', 'status': 'Invited', 'assignments_completed': 0}
            ]
            
            df = pd.DataFrame(mock_students)
            st.dataframe(df, use_container_width=True)
            
            if st.button("Done Managing"):
                st.session_state.manage_class = False
                st.rerun()

def show_assignments_page():
    st.subheader("📝 Create Assignment")
    
    # Select class
    class_names = [c['name'] for c in MOCK_CLASSES]
    if not class_names:
        st.warning("Please create a class first!")
        return
    
    selected_class_name = st.selectbox("Select Class", class_names)
    selected_class = next(c for c in MOCK_CLASSES if c['name'] == selected_class_name)
    
    # Assignment details
    col1, col2 = st.columns(2)
    with col1:
        assignment_name = st.text_input("Assignment Name", placeholder="e.g., Week 3 - Arrays and Strings")
    with col2:
        due_date = st.date_input("Due Date", min_value=datetime.now().date())
    
    st.markdown("### Search Questions")
    
    # Search interface
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search_query = st.text_input("Search questions", placeholder="e.g., dynamic programming, arrays, SQL")
    with col2:
        difficulty = st.selectbox("Difficulty", ["All", "Easy", "Medium", "Hard"])
    with col3:
        category = st.selectbox("Category", ["All", "Arrays", "Trees", "DP", "SQL", "Graphs", "Strings", "Heaps"])
    
    # Filter questions
    filtered_questions = MOCK_QUESTIONS
    if difficulty != "All":
        filtered_questions = [q for q in filtered_questions if q['difficulty'] == difficulty]
    if category != "All":
        filtered_questions = [q for q in filtered_questions if q['category'] == category]
    if search_query:
        filtered_questions = [q for q in filtered_questions if search_query.lower() in q['title'].lower()]
    
    # Display questions
    st.markdown("### Available Questions")
    
    for question in filtered_questions:
        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
        
        with col1:
            st.write(f"**{question['title']}**")
        with col2:
            st.caption(question['category'])
        with col3:
            difficulty_color = {'Easy': '🟢', 'Medium': '🟡', 'Hard': '🔴'}
            st.write(f"{difficulty_color[question['difficulty']]} {question['difficulty']}")
        with col4:
            st.caption(f"{question['completion_rate']}% success")
        with col5:
            if st.button("Add", key=f"add_{question['id']}"):
                if question not in st.session_state.selected_questions:
                    st.session_state.selected_questions.append(question)
                    st.success(f"Added {question['title']}")
                    st.rerun()
    
    # Selected questions
    if st.session_state.selected_questions:
        st.markdown("### Selected Questions")
        
        for idx, question in enumerate(st.session_state.selected_questions):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"{idx + 1}. **{question['title']}** ({question['difficulty']})")
            with col2:
                points = st.number_input("Points", min_value=0, max_value=100, value=10, 
                                       key=f"points_{question['id']}")
            with col3:
                if st.button("Remove", key=f"remove_{question['id']}"):
                    st.session_state.selected_questions.remove(question)
                    st.rerun()
        
        st.divider()
        
        # Create assignment
        if st.button("Create Assignment", type="primary", use_container_width=True):
            if assignment_name and st.session_state.selected_questions:
                # Mock assignment creation
                st.success(f"Assignment '{assignment_name}' created with {len(st.session_state.selected_questions)} questions!")
                
                # Show sample email
                with st.expander("Sample Student Email"):
                    st.markdown("""
                    **Subject:** New Assignment: {assignment_name}
                    
                    Dear Student,
                    
                    You have a new assignment due on {due_date}.
                    
                    **Questions:**
                    """.format(assignment_name=assignment_name, due_date=due_date))
                    
                    for q in st.session_state.selected_questions:
                        link = create_signed_link(q['id'], 1, "student@university.edu")
                        st.markdown(f"- [{q['title']}]({link})")
                    
                    st.markdown("\nGood luck!")
                
                # Clear selection
                st.session_state.selected_questions = []
                st.rerun()

def show_progress_page():
    st.subheader("📊 Student Progress")
    
    # Select class
    class_names = [c['name'] for c in MOCK_CLASSES]
    if not class_names:
        st.warning("No classes found!")
        return
    
    selected_class_name = st.selectbox("Select Class", class_names)
    
    # Mock assignment data
    assignments = [
        {'name': 'Week 1 - Arrays', 'due_date': '2025-01-20', 'questions': 5, 'avg_completion': 78},
        {'name': 'Week 2 - Trees', 'due_date': '2025-01-27', 'questions': 4, 'avg_completion': 65},
        {'name': 'Week 3 - Dynamic Programming', 'due_date': '2025-02-03', 'questions': 3, 'avg_completion': 45}
    ]
    
    # Display assignments
    for assignment in assignments:
        with st.expander(f"{assignment['name']} - Due: {assignment['due_date']}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Questions", assignment['questions'])
            with col2:
                st.metric("Avg Completion", f"{assignment['avg_completion']}%")
            with col3:
                st.metric("Students Submitted", f"{int(assignment['avg_completion'] * 0.3)}/30")
            
            # Mock student progress data
            student_data = pd.DataFrame({
                'Student': ['student1@u.edu', 'student2@u.edu', 'student3@u.edu', 'student4@u.edu'],
                'Q1': ['✅', '✅', '❌', '✅'],
                'Q2': ['✅', '❌', '❌', '✅'],
                'Q3': ['✅', '✅', '✅', '❌'],
                'Score': [30, 20, 10, 20],
                'Attempts': [3, 5, 2, 4]
            })
            
            st.dataframe(student_data, use_container_width=True)
            
            # Visualizations
            col1, col2 = st.columns(2)
            
            with col1:
                # Completion rate by question
                fig = px.bar(
                    x=['Q1', 'Q2', 'Q3'],
                    y=[75, 50, 75],
                    title="Completion Rate by Question",
                    labels={'x': 'Question', 'y': 'Completion %'}
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Score distribution
                fig = px.histogram(
                    x=[30, 30, 20, 20, 20, 10, 10, 0, 0],
                    nbins=4,
                    title="Score Distribution",
                    labels={'x': 'Score', 'y': 'Students'}
                )
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)

def show_reports_page():
    st.subheader("📄 Export Reports")
    
    # Select class and assignment
    class_names = [c['name'] for c in MOCK_CLASSES]
    if not class_names:
        st.warning("No classes found!")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_class = st.selectbox("Select Class", class_names)
    
    with col2:
        assignments = ['Week 1 - Arrays', 'Week 2 - Trees', 'Week 3 - DP']
        selected_assignment = st.selectbox("Select Assignment", assignments)
    
    st.markdown("### Report Preview")
    
    # Mock report data
    with st.container():
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        
        st.markdown(f"## {selected_assignment} Report")
        st.markdown(f"**Class:** {selected_class}")
        st.markdown(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Students", 30)
        with col2:
            st.metric("Submitted", 24)
        with col3:
            st.metric("Average Score", "72%")
        with col4:
            st.metric("Completion Rate", "80%")
        
        st.markdown("### Question Performance")
        
        question_stats = pd.DataFrame({
            'Question': ['Two Sum', 'Binary Tree', 'Knapsack Problem'],
            'Attempts': [89, 72, 45],
            'Success Rate': ['85%', '65%', '40%'],
            'Avg Time': ['12 min', '25 min', '35 min']
        })
        
        st.dataframe(question_stats, use_container_width=True)
        
        st.markdown("### Top Performers")
        
        top_students = pd.DataFrame({
            'Rank': [1, 2, 3],
            'Student': ['student1@u.edu', 'student4@u.edu', 'student7@u.edu'],
            'Score': [100, 95, 90],
            'Time': ['45 min', '52 min', '48 min']
        })
        
        st.dataframe(top_students, use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.divider()
    
    # Export options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Export as PDF", type="primary", use_container_width=True):
            st.success("PDF report generated! Download link sent to your email.")
    
    with col2:
        if st.button("📊 Export as Excel", use_container_width=True):
            st.success("Excel report generated! Download link sent to your email.")
    
    with col3:
        if st.button("📧 Email to Students", use_container_width=True):
            st.success("Report emailed to all students!")

# Main app logic
def main():
    if not st.session_state.authenticated:
        show_auth()
    else:
        show_portal()

if __name__ == "__main__":
    main()