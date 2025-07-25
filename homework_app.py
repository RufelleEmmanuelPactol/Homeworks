import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
from toolkits.db import run_query
from toolkits.email.mail import send_email

# Page config
st.set_page_config(
    page_title="Interview Query Homeworks",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .success-card {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #28a745;
    }
    .warning-card {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #ffc107;
    }
    .sidebar-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'user_type' not in st.session_state:
    st.session_state.user_type = None

def fake_login():
    """Fake authentication system"""
    st.markdown('<div class="sidebar-header">🔐 Login</div>', unsafe_allow_html=True)
    
    email = st.text_input("Email", key="login_email")
    user_type = st.selectbox("Login as:", ["Instructor", "Student"], key="login_type")
    
    if st.button("Login", type="primary"):
        if email:
            st.session_state.authenticated = True
            st.session_state.user_email = email
            st.session_state.user_type = user_type
            st.rerun()
        else:
            st.error("Please enter an email")

def logout():
    """Logout function"""
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.session_state.user_type = None
        st.rerun()

def get_or_create_instructor(email):
    """Get or create instructor in database"""
    try:
        # Check if instructor exists
        result = run_query(f"SELECT id FROM hackathon_2025_instructors WHERE email = '{email}'")
        if not result.empty:
            return result.iloc[0]['id']
        
        # Create new instructor
        run_query(f"""
            INSERT INTO hackathon_2025_instructors (email, last_login) 
            VALUES ('{email}', NOW())
        """)
        
        # Get the new instructor ID
        result = run_query(f"SELECT id FROM hackathon_2025_instructors WHERE email = '{email}'")
        return result.iloc[0]['id']
    except Exception as e:
        st.error(f"Database error: {e}")
        return None

def instructor_dashboard():
    """Main instructor dashboard"""
    st.markdown('<div class="main-header">📚 Interview Query Homeworks</div>', unsafe_allow_html=True)
    
    instructor_id = get_or_create_instructor(st.session_state.user_email)
    if not instructor_id:
        st.error("Failed to initialize instructor account")
        return
    
    # Sidebar navigation
    st.sidebar.markdown('<div class="sidebar-header">📋 Navigation</div>', unsafe_allow_html=True)
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["Dashboard", "Manage Classes", "Create Assignment", "View Progress", "Settings"]
    )
    
    if page == "Dashboard":
        show_dashboard(instructor_id)
    elif page == "Manage Classes":
        manage_classes(instructor_id)
    elif page == "Create Assignment":
        create_assignment(instructor_id)
    elif page == "View Progress":
        view_progress(instructor_id)
    elif page == "Settings":
        show_settings()

def show_dashboard(instructor_id):
    """Show instructor dashboard overview"""
    st.subheader("📊 Dashboard Overview")
    
    try:
        # Get instructor stats
        classes = run_query(f"""
            SELECT COUNT(*) as total_classes 
            FROM hackathon_2025_instructor_classes 
            WHERE instructor_id = {instructor_id} AND is_active = 1
        """)
        
        students = run_query(f"""
            SELECT COUNT(DISTINCT cm.email) as total_students
            FROM hackathon_2025_class_members cm
            JOIN hackathon_2025_instructor_classes ic ON cm.class_id = ic.id
            WHERE ic.instructor_id = {instructor_id} AND cm.is_active = 1
        """)
        
        assignments = run_query(f"""
            SELECT COUNT(*) as total_assignments
            FROM hackathon_2025_assignments a
            JOIN hackathon_2025_instructor_classes ic ON a.class_id = ic.id
            WHERE ic.instructor_id = {instructor_id} AND a.is_active = 1
        """)
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Classes", classes.iloc[0]['total_classes'] if not classes.empty else 0)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Students", students.iloc[0]['total_students'] if not students.empty else 0)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.metric("Total Assignments", assignments.iloc[0]['total_assignments'] if not assignments.empty else 0)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Recent activity
        st.subheader("📈 Recent Activity")
        
        recent_classes = run_query(f"""
            SELECT class_name, created_at
            FROM hackathon_2025_instructor_classes
            WHERE instructor_id = {instructor_id} AND is_active = 1
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if not recent_classes.empty:
            st.dataframe(recent_classes, use_container_width=True)
        else:
            st.info("No classes created yet. Start by creating your first class!")
            
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")

def manage_classes(instructor_id):
    """Manage classes interface"""
    st.subheader("🏫 Manage Classes")
    
    tab1, tab2 = st.tabs(["📝 Create New Class", "📋 Existing Classes"])
    
    with tab1:
        create_class_form(instructor_id)
    
    with tab2:
        show_existing_classes(instructor_id)

def create_class_form(instructor_id):
    """Form to create a new class"""
    st.write("### Create New Class")
    
    with st.form("create_class"):
        class_name = st.text_input("Class Name", placeholder="e.g., Data Science 101")
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Add Students:**")
            add_method = st.radio("Choose method:", ["Upload CSV", "Manual Entry"])
        
        students_data = None
        if add_method == "Upload CSV":
            uploaded_file = st.file_uploader(
                "Upload CSV file with student emails", 
                type=['csv'],
                help="CSV should have a column named 'email' with student email addresses"
            )
            
            if uploaded_file:
                try:
                    df = pd.read_csv(uploaded_file)
                    if 'email' in df.columns:
                        students_data = df['email'].dropna().tolist()
                        st.success(f"Found {len(students_data)} valid email addresses")
                        st.dataframe(df[['email']], use_container_width=True)
                    else:
                        st.error("CSV must contain an 'email' column")
                except Exception as e:
                    st.error(f"Error reading CSV: {e}")
        
        else:  # Manual Entry
            manual_emails = st.text_area(
                "Enter student emails (one per line)",
                placeholder="student1@university.edu\nstudent2@university.edu"
            )
            if manual_emails:
                students_data = [email.strip() for email in manual_emails.split('\n') if email.strip()]
        
        submitted = st.form_submit_button("Create Class", type="primary")
        
        if submitted and class_name:
            try:
                # Create class
                run_query(f"""
                    INSERT INTO hackathon_2025_instructor_classes (instructor_id, class_name)
                    VALUES ({instructor_id}, '{class_name}')
                """)
                
                # Get class ID
                class_result = run_query(f"""
                    SELECT id FROM hackathon_2025_instructor_classes 
                    WHERE instructor_id = {instructor_id} AND class_name = '{class_name}'
                    ORDER BY created_at DESC LIMIT 1
                """)
                
                if not class_result.empty:
                    class_id = class_result.iloc[0]['id']
                    
                    # Add students if provided
                    if students_data:
                        for email in students_data:
                            run_query(f"""
                                INSERT INTO hackathon_2025_class_members (class_id, email)
                                VALUES ({class_id}, '{email}')
                            """)
                    
                    st.markdown('<div class="success-card">', unsafe_allow_html=True)
                    st.success(f"✅ Class '{class_name}' created successfully with {len(students_data) if students_data else 0} students!")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Send invitation emails
                    if students_data and st.button("Send Invitation Emails"):
                        send_invitations(students_data, class_name)
                        
            except Exception as e:
                st.error(f"Error creating class: {e}")

def show_existing_classes(instructor_id):
    """Show existing classes with management options"""
    try:
        classes = run_query(f"""
            SELECT ic.id, ic.class_name, ic.created_at,
                   COUNT(cm.id) as student_count
            FROM hackathon_2025_instructor_classes ic
            LEFT JOIN hackathon_2025_class_members cm ON ic.id = cm.class_id AND cm.is_active = 1
            WHERE ic.instructor_id = {instructor_id} AND ic.is_active = 1
            GROUP BY ic.id, ic.class_name, ic.created_at
            ORDER BY ic.created_at DESC
        """)
        
        if not classes.empty:
            for _, class_row in classes.iterrows():
                with st.expander(f"📚 {class_row['class_name']} ({class_row['student_count']} students)"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Created:** {class_row['created_at']}")
                        st.write(f"**Students:** {class_row['student_count']}")
                    
                    with col2:
                        if st.button(f"View Students", key=f"view_{class_row['id']}"):
                            show_class_students(class_row['id'])
                    
                    with col3:
                        if st.button(f"Add Students", key=f"add_{class_row['id']}"):
                            add_students_to_class(class_row['id'])
        else:
            st.info("No classes created yet.")
            
    except Exception as e:
        st.error(f"Error loading classes: {e}")

def show_class_students(class_id):
    """Show students in a specific class"""
    try:
        students = run_query(f"""
            SELECT email, invited_at, joined_at, is_active
            FROM hackathon_2025_class_members
            WHERE class_id = {class_id}
            ORDER BY invited_at DESC
        """)
        
        if not students.empty:
            st.dataframe(students, use_container_width=True)
        else:
            st.info("No students in this class yet.")
            
    except Exception as e:
        st.error(f"Error loading students: {e}")

def add_students_to_class(class_id):
    """Add students to an existing class"""
    st.write("### Add Students to Class")
    
    with st.form(f"add_students_{class_id}"):
        add_method = st.radio("Choose method:", ["Upload CSV", "Manual Entry"], key=f"add_method_{class_id}")
        
        students_data = None
        if add_method == "Upload CSV":
            uploaded_file = st.file_uploader(
                "Upload CSV file with student emails", 
                type=['csv'],
                key=f"upload_{class_id}",
                help="CSV should have a column named 'email' with student email addresses"
            )
            
            if uploaded_file:
                try:
                    df = pd.read_csv(uploaded_file)
                    if 'email' in df.columns:
                        students_data = df['email'].dropna().tolist()
                        st.success(f"Found {len(students_data)} valid email addresses")
                        st.dataframe(df[['email']], use_container_width=True)
                    else:
                        st.error("CSV must contain an 'email' column")
                except Exception as e:
                    st.error(f"Error reading CSV: {e}")
        
        else:  # Manual Entry
            manual_emails = st.text_area(
                "Enter student emails (one per line)",
                placeholder="student1@university.edu\nstudent2@university.edu",
                key=f"manual_{class_id}"
            )
            if manual_emails:
                students_data = [email.strip() for email in manual_emails.split('\n') if email.strip()]
        
        submitted = st.form_submit_button("Add Students", type="primary")
        
        if submitted and students_data:
            try:
                added_count = 0
                for email in students_data:
                    # Check if student already exists in class
                    existing = run_query(f"""
                        SELECT id FROM hackathon_2025_class_members 
                        WHERE class_id = {class_id} AND email = '{email}'
                    """)
                    
                    if existing.empty:
                        run_query(f"""
                            INSERT INTO hackathon_2025_class_members (class_id, email)
                            VALUES ({class_id}, '{email}')
                        """)
                        added_count += 1
                
                st.success(f"✅ Added {added_count} new students to the class!")
                if added_count < len(students_data):
                    st.info(f"{len(students_data) - added_count} students were already in the class.")
                        
            except Exception as e:
                st.error(f"Error adding students: {e}")

def send_invitations(email_list, class_name):
    """Send invitation emails to students"""
    try:
        for email in email_list:
            subject = f"Invitation to join {class_name} on Interview Query"
            body = f"""
            <h2>Welcome to {class_name}!</h2>
            <p>You've been invited to join the class "{class_name}" on Interview Query Homeworks platform.</p>
            <p>To get started, please log in with your email address: {email}</p>
            <p>Best regards,<br>Interview Query Team</p>
            """
            
            send_email("noreply@interviewquery.com", email, subject, body)
        
        st.success(f"✅ Invitation emails sent to {len(email_list)} students!")
        
    except Exception as e:
        st.error(f"Error sending invitations: {e}")

def create_assignment(instructor_id):
    """Create assignment interface"""
    st.subheader("📝 Create Assignment")
    
    # Get instructor's classes
    try:
        classes = run_query(f"""
            SELECT id, class_name
            FROM hackathon_2025_instructor_classes
            WHERE instructor_id = {instructor_id} AND is_active = 1
            ORDER BY class_name
        """)
        
        if classes.empty:
            st.warning("You need to create a class first before creating assignments.")
            return
        
        with st.form("create_assignment"):
            col1, col2 = st.columns(2)
            
            with col1:
                selected_class = st.selectbox(
                    "Select Class",
                    options=classes['id'].tolist(),
                    format_func=lambda x: classes[classes['id'] == x]['class_name'].iloc[0]
                )
                
                assignment_name = st.text_input(
                    "Assignment Name",
                    placeholder="e.g., SQL Basics Practice"
                )
            
            with col2:
                due_date = st.date_input("Due Date", value=datetime.now() + timedelta(days=7))
                due_time = st.time_input("Due Time", value=datetime.now().replace(hour=23, minute=59).time())
            
            st.write("### 📋 Assignment Questions")
            st.info("For demo purposes, we'll use mock question IDs. In production, this would integrate with Interview Query's question database.")
            
            # Mock question selection
            question_ids = st.text_area(
                "Question IDs (comma-separated)",
                placeholder="1001, 1002, 1003",
                help="Enter Interview Query question IDs separated by commas"
            )
            
            default_points = st.number_input("Default Points per Question", min_value=1, value=10)
            
            submitted = st.form_submit_button("Create Assignment", type="primary")
            
            if submitted and assignment_name and question_ids:
                try:
                    # Combine date and time
                    due_datetime = datetime.combine(due_date, due_time)
                    
                    # Create assignment
                    run_query(f"""
                        INSERT INTO hackathon_2025_assignments (class_id, name, due_date)
                        VALUES ({selected_class}, '{assignment_name}', '{due_datetime}')
                    """)
                    
                    # Get assignment ID
                    assignment_result = run_query(f"""
                        SELECT id FROM hackathon_2025_assignments
                        WHERE class_id = {selected_class} AND name = '{assignment_name}'
                        ORDER BY created_at DESC LIMIT 1
                    """)
                    
                    if not assignment_result.empty:
                        assignment_id = assignment_result.iloc[0]['id']
                        
                        # Add questions to assignment
                        question_list = [q.strip() for q in question_ids.split(',') if q.strip()]
                        for question_id in question_list:
                            run_query(f"""
                                INSERT INTO hackathon_2025_assignment_questions (assignment_id, question_id, points)
                                VALUES ({assignment_id}, {question_id}, {default_points})
                            """)
                        
                        st.markdown('<div class="success-card">', unsafe_allow_html=True)
                        st.success(f"✅ Assignment '{assignment_name}' created successfully with {len(question_list)} questions!")
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Initialize progress tracking for all students in the class
                        students = run_query(f"""
                            SELECT email FROM hackathon_2025_class_members
                            WHERE class_id = {selected_class} AND is_active = 1
                        """)
                        
                        for _, student in students.iterrows():
                            for question_id in question_list:
                                run_query(f"""
                                    INSERT IGNORE INTO hackathon_2025_student_progress 
                                    (assignment_id, student_email, question_id)
                                    VALUES ({assignment_id}, '{student['email']}', {question_id})
                                """)
                        
                        st.info(f"Progress tracking initialized for {len(students)} students.")
                        
                except Exception as e:
                    st.error(f"Error creating assignment: {e}")
    
    except Exception as e:
        st.error(f"Error loading classes: {e}")
    
    # Show existing assignments
    st.write("---")
    st.subheader("📚 Existing Assignments")
    show_existing_assignments(instructor_id)

def show_existing_assignments(instructor_id):
    """Show existing assignments for instructor"""
    try:
        assignments = run_query(f"""
            SELECT a.id, a.name, a.due_date, ic.class_name,
                   COUNT(aq.id) as question_count,
                   COUNT(DISTINCT sp.student_email) as student_count
            FROM hackathon_2025_assignments a
            JOIN hackathon_2025_instructor_classes ic ON a.class_id = ic.id
            LEFT JOIN hackathon_2025_assignment_questions aq ON a.id = aq.assignment_id
            LEFT JOIN hackathon_2025_student_progress sp ON a.id = sp.assignment_id
            WHERE ic.instructor_id = {instructor_id} AND a.is_active = 1
            GROUP BY a.id, a.name, a.due_date, ic.class_name
            ORDER BY a.due_date DESC
        """)
        
        if not assignments.empty:
            for _, assignment in assignments.iterrows():
                with st.expander(f"📝 {assignment['name']} - {assignment['class_name']}"):
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.write(f"**Due:** {assignment['due_date']}")
                    with col2:
                        st.write(f"**Questions:** {assignment['question_count']}")
                    with col3:
                        st.write(f"**Students:** {assignment['student_count']}")
                    with col4:
                        if st.button(f"View Details", key=f"view_assignment_{assignment['id']}"):
                            show_assignment_details(assignment['id'])
        else:
            st.info("No assignments created yet.")
            
    except Exception as e:
        st.error(f"Error loading assignments: {e}")

def show_assignment_details(assignment_id):
    """Show detailed assignment information"""
    try:
        # Get assignment info
        assignment_info = run_query(f"""
            SELECT a.name, a.due_date, ic.class_name
            FROM hackathon_2025_assignments a
            JOIN hackathon_2025_instructor_classes ic ON a.class_id = ic.id
            WHERE a.id = {assignment_id}
        """)
        
        if not assignment_info.empty:
            assignment = assignment_info.iloc[0]
            st.write(f"### Assignment: {assignment['name']}")
            st.write(f"**Class:** {assignment['class_name']}")
            st.write(f"**Due Date:** {assignment['due_date']}")
            
            # Get questions
            questions = run_query(f"""
                SELECT question_id, points
                FROM hackathon_2025_assignment_questions
                WHERE assignment_id = {assignment_id}
            """)
            
            if not questions.empty:
                st.write("**Questions:**")
                st.dataframe(questions, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error loading assignment details: {e}")

def view_progress(instructor_id):
    """View student progress"""
    st.subheader("📊 Student Progress")
    
    try:
        # Get instructor's assignments
        assignments = run_query(f"""
            SELECT a.id, a.name, ic.class_name
            FROM hackathon_2025_assignments a
            JOIN hackathon_2025_instructor_classes ic ON a.class_id = ic.id
            WHERE ic.instructor_id = {instructor_id} AND a.is_active = 1
            ORDER BY a.due_date DESC
        """)
        
        if assignments.empty:
            st.info("No assignments found. Create an assignment first to track progress.")
            return
        
        # Assignment selector
        selected_assignment = st.selectbox(
            "Select Assignment",
            options=assignments['id'].tolist(),
            format_func=lambda x: f"{assignments[assignments['id'] == x]['name'].iloc[0]} - {assignments[assignments['id'] == x]['class_name'].iloc[0]}"
        )
        
        if selected_assignment:
            show_assignment_progress(selected_assignment)
            
    except Exception as e:
        st.error(f"Error loading progress data: {e}")

def show_assignment_progress(assignment_id):
    """Show progress for a specific assignment"""
    try:
        # Get assignment details
        assignment_info = run_query(f"""
            SELECT a.name, a.due_date, ic.class_name
            FROM hackathon_2025_assignments a
            JOIN hackathon_2025_instructor_classes ic ON a.class_id = ic.id
            WHERE a.id = {assignment_id}
        """)
        
        if assignment_info.empty:
            st.error("Assignment not found")
            return
        
        assignment = assignment_info.iloc[0]
        st.write(f"### Progress for: {assignment['name']}")
        st.write(f"**Class:** {assignment['class_name']} | **Due:** {assignment['due_date']}")
        
        # Get progress summary by querying submission tables directly
        progress_summary = run_query(f"""
            SELECT 
                sp.student_email,
                cm.user_id,
                COUNT(DISTINCT sp.question_id) as total_questions,
                COUNT(DISTINCT CASE 
                    WHEN q.type IN ('sql', 'python', 'algorithms') AND ucr.is_accepted = 1 THEN sp.question_id
                    WHEN q.type NOT IN ('sql', 'python', 'algorithms') AND ts.score >= 0.8 THEN sp.question_id
                END) as completed_questions,
                ROUND(AVG(
                    CASE 
                        WHEN q.type IN ('sql', 'python', 'algorithms') THEN COALESCE(ucr.is_accepted, 0)
                        ELSE COALESCE(ts.score, 0)
                    END
                ), 2) as avg_score,
                COUNT(DISTINCT CASE 
                    WHEN ucr.question_id IS NOT NULL OR ts.question_id IS NOT NULL THEN sp.question_id 
                END) as attempted_questions
            FROM hackathon_2025_student_progress sp
            JOIN hackathon_2025_class_members cm ON sp.student_email = cm.email
            JOIN questions q ON sp.question_id = q.id
            LEFT JOIN (
                SELECT user_id, question_id, MAX(is_accepted) as is_accepted
                FROM user_code_runs
                GROUP BY user_id, question_id
            ) ucr ON cm.user_id = ucr.user_id AND sp.question_id = ucr.question_id AND q.type IN ('sql', 'python', 'algorithms')
            LEFT JOIN (
                SELECT user_id, question_id, MAX(score) as score
                FROM text_submissions
                GROUP BY user_id, question_id
            ) ts ON cm.user_id = ts.user_id AND sp.question_id = ts.question_id AND q.type NOT IN ('sql', 'python', 'algorithms')
            WHERE sp.assignment_id = {assignment_id}
            GROUP BY sp.student_email, cm.user_id
            ORDER BY completed_questions DESC, avg_score DESC
        """)
        
        if not progress_summary.empty:
            # Calculate completion percentage
            progress_summary['completion_rate'] = (
                progress_summary['completed_questions'] / progress_summary['total_questions'] * 100
            ).round(1)
            
            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Total Students", len(progress_summary))
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                avg_completion = progress_summary['completion_rate'].mean()
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Avg Completion", f"{avg_completion:.1f}%")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col3:
                students_completed = len(progress_summary[progress_summary['completion_rate'] == 100])
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Fully Completed", students_completed)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col4:
                avg_score = progress_summary['avg_score'].mean()
                st.markdown('<div class="metric-card">', unsafe_allow_html=True)
                st.metric("Avg Score", f"{avg_score:.1f}" if not pd.isna(avg_score) else "N/A")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Progress table
            st.write("### 📈 Student Progress Details")
            
            # Color code based on completion rate
            def color_completion_rate(val):
                if val >= 80:
                    return 'background-color: #d4edda'  # Green
                elif val >= 50:
                    return 'background-color: #fff3cd'  # Yellow
                else:
                    return 'background-color: #f8d7da'  # Red
            
            styled_df = progress_summary.style.applymap(
                color_completion_rate, subset=['completion_rate']
            )
            
            st.dataframe(styled_df, use_container_width=True)
            
            # Detailed progress by question
            st.write("### 📋 Question-by-Question Breakdown")
            
            detailed_progress = run_query(f"""
                SELECT 
                    aq.question_id,
                    q.title,
                    q.type,
                    aq.points,
                    COUNT(DISTINCT cm.user_id) as total_students,
                    COUNT(DISTINCT CASE 
                        WHEN q.type IN ('sql', 'python', 'algorithms') AND ucr.is_accepted = 1 THEN cm.user_id
                        WHEN q.type NOT IN ('sql', 'python', 'algorithms') AND ts.score >= 0.8 THEN cm.user_id
                    END) as completed_count,
                    ROUND(AVG(CASE 
                        WHEN q.type IN ('sql', 'python', 'algorithms') THEN ucr.attempt_count
                        ELSE ts.attempt_count
                    END), 1) as avg_attempts,
                    ROUND(AVG(CASE 
                        WHEN q.type IN ('sql', 'python', 'algorithms') THEN ucr.is_accepted
                        ELSE ts.score
                    END), 2) as avg_score
                FROM hackathon_2025_assignment_questions aq
                JOIN questions q ON aq.question_id = q.id
                JOIN hackathon_2025_assignments a ON aq.assignment_id = a.id
                JOIN hackathon_2025_class_members cm ON cm.class_id = a.class_id AND cm.is_active = 1
                LEFT JOIN (
                    SELECT user_id, question_id, 
                           MAX(is_accepted) as is_accepted,
                           COUNT(*) as attempt_count
                    FROM user_code_runs
                    GROUP BY user_id, question_id
                ) ucr ON cm.user_id = ucr.user_id AND aq.question_id = ucr.question_id
                LEFT JOIN (
                    SELECT user_id, question_id, 
                           MAX(score) as score,
                           COUNT(*) as attempt_count
                    FROM text_submissions
                    GROUP BY user_id, question_id
                ) ts ON cm.user_id = ts.user_id AND aq.question_id = ts.question_id
                WHERE aq.assignment_id = {assignment_id}
                GROUP BY aq.question_id, q.title, q.type, aq.points
                ORDER BY aq.question_id
            """)
            
            if not detailed_progress.empty:
                detailed_progress['completion_rate'] = (
                    detailed_progress['completed_count'] / detailed_progress['total_students'] * 100
                ).round(1)
                
                st.dataframe(detailed_progress, use_container_width=True)
        else:
            st.info("No student progress data available for this assignment.")
            
    except Exception as e:
        st.error(f"Error loading assignment progress: {e}")

def show_settings():
    """Settings page"""
    st.subheader("⚙️ Settings")
    st.info("Settings page - Coming soon!")

def student_dashboard():
    """Student dashboard"""
    st.markdown('<div class="main-header">📚 My Assignments</div>', unsafe_allow_html=True)
    st.info("Student dashboard - Coming soon!")

# Main app logic
def main():
    if not st.session_state.authenticated:
        st.sidebar.markdown('<div class="main-header">🎓 Interview Query<br>Homeworks</div>', unsafe_allow_html=True)
        fake_login()
        
        # Landing page content
        st.markdown('<div class="main-header">📚 Welcome to Interview Query Homeworks</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""
            ### 👩‍🏫 For Instructors
            - Create and manage classes
            - Assign Interview Query content as homework
            - Track student progress and engagement
            - Improve adoption rates in your courses
            """)
        
        with col2:
            st.markdown("""
            ### 👨‍🎓 For Students
            - Access assigned homework and practice problems
            - Track your progress and scores
            - Get instant feedback on your solutions
            - Prepare for technical interviews
            """)
        
        st.markdown("""
        ---
        ### 🚀 Getting Started
        Please log in using the sidebar to access your dashboard.
        """)
        
    else:
        # Show user info and logout in sidebar
        st.sidebar.markdown('<div class="sidebar-header">👤 User Info</div>', unsafe_allow_html=True)
        st.sidebar.write(f"**Email:** {st.session_state.user_email}")
        st.sidebar.write(f"**Role:** {st.session_state.user_type}")
        logout()
        
        # Show appropriate dashboard
        if st.session_state.user_type == "Instructor":
            instructor_dashboard()
        else:
            student_dashboard()

if __name__ == "__main__":
    main()