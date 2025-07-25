import dotenv
dotenv.load_dotenv()
import streamlit as st
import pandas as pd
import requests
import hashlib
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from toolkits.controllers.users import get_users, get_classes
from toolkits.db import run_query, execute_query
from toolkits.email.mail import send_email
from toolkits.email.templates import get_class_invitation_template, get_assignment_notification_template

# Page configuration
st.set_page_config(
    page_title="Interview Query - Instructor Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced Interview Query Design System CSS
st.markdown("""

""", unsafe_allow_html=True)

def create_signed_link(question_url: str, assignment_id: int, user_email: str) -> str:
    """Create signed link for question access"""
    timestamp = int(datetime.now().timestamp())
    data = f"{question_url}:{assignment_id}:{user_email}:{timestamp}"
    signature = hashlib.sha256(data.encode()).hexdigest()[:16]
    
    # Append parameters correctly based on whether URL already has query params
    separator = '&' if '?' in question_url else '?'
    return f"{question_url}{separator}hw={assignment_id}&u={signature}"


def show_classes_page(user):
    st.markdown('<h2 class="main-header">📚 My Classes</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color: var(--iq-gray-600); font-size: 1.125rem; margin-bottom: 2rem;">Manage your classes and student rosters</p>', unsafe_allow_html=True)

    # Create new class with enhanced UI
    with st.expander("✨ Create New Class", expanded=False):
        col1, col2 = st.columns([3, 1])
        with col1:
            class_name = st.text_input("Class Name", placeholder="e.g., Data Structures Fall 2025")
        with col2:
            st.write("") # Spacer
            if st.button("Create Class", type="primary", use_container_width=True):
                if class_name:
                    try:
                        query = f"INSERT INTO hackathon_2025_instructor_classes (user_id, class_name) VALUES ({user.id}, '{class_name}')"
                        execute_query(query)
                        st.success(f"🎉 Class '{class_name}' created successfully!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error creating class: {str(e)}")

    # Display existing classes
    try:
        classes = get_classes(user)
        if len(classes) > 0:
            for _, class_data in classes.iterrows():
                # Use a custom card component
                card_html = f"""
                <div class="metric-card" style="margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h3 style="margin: 0; color: var(--iq-gray-800); font-weight: 600;">{class_data['class_name']}</h3>
                            <p style="margin: 0.25rem 0 0 0; color: var(--iq-gray-600); font-size: 0.875rem;">Created: {class_data['created_at']}</p>
                        </div>
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)

                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                    with col1:
                        st.write("")  # Spacer

                    with col2:
                        # Get student count
                        try:
                            student_count = run_query(f"SELECT COUNT(*) as count FROM hackathon_2025_class_members WHERE class_id = {class_data['id']}")
                            count = student_count.iloc[0]['count'] if len(student_count) > 0 else 0
                        except:
                            count = 0
                        st.metric("Students", count)

                    with col3:
                        if st.button("Manage", key=f"manage_{class_data['id']}"):
                            st.session_state.selected_class = class_data['id']
                            st.session_state.manage_class = True
                            st.rerun()

                    with col4:
                        if st.button("Delete", key=f"delete_{class_data['id']}"):
                            try:
                                execute_query(f"DELETE FROM hackathon_2025_instructor_classes WHERE id = {class_data['id']}")
                                st.success("Class deleted!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error deleting class: {str(e)}")

                    st.divider()
        else:
            st.info("No classes found. Create your first class above!")
    except Exception as e:
        st.error(f"Error loading classes: {str(e)}")

    # Enhanced class management section
    if st.session_state.get('manage_class'):
        try:
            classes = get_classes(user)
            selected_class = classes[classes['id'] == st.session_state.selected_class].iloc[0]

            st.markdown("---")
            
            # Class management header with gradient
            header_html = f"""
            <div style="margin-bottom: 2rem;">
                <h2 class="sub-header">Managing: {selected_class['class_name']}</h2>
            </div>
            """
            st.markdown(header_html, unsafe_allow_html=True)

            # Student roster management with tabs
            tab1, tab2, tab3 = st.tabs(["👥 Students", "📝 Assignments", "📊 Analytics"])
            
            with tab1:
                st.markdown("### Student Roster")
                
                # Add students with enhanced UI
                with st.expander("➕ Add Students", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        student_emails = st.text_area("Enter student emails (one per line)",
                                                    placeholder="student1@university.edu\nstudent2@university.edu",
                                                    height=120)
                    with col2:
                        st.write("") # spacer
                        st.write("") # spacer
                        if st.button("Add & Invite", type="primary", use_container_width=True):
                            if student_emails:
                                emails = [e.strip() for e in student_emails.split('\n') if e.strip()]
                                try:
                                    # First validate all emails can be sent before adding any students
                                    progress_bar = st.progress(0, text="Adding students...")
                                    for i, email in enumerate(emails):
                                        # Add to database
                                        query = f"INSERT INTO hackathon_2025_class_members (class_id, email) VALUES ({selected_class['id']}, '{email}')"
                                        execute_query(query)
                                        
                                        # Send invitation email
                                        subject = f"🎓 Welcome to {selected_class['class_name']} - Interview Query"
                                        html_body = get_class_invitation_template(
                                            class_name=selected_class['class_name'],
                                            student_email=email,
                                            instructor_email=user.email
                                        )
                                        send_email("noreply@interviewquery.com", email, subject, html_body)
                                        
                                        progress_bar.progress((i + 1) / len(emails), text=f"Added {i + 1}/{len(emails)} students")
                                    
                                    st.success(f"✅ Added {len(emails)} students and sent invitation emails!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")

                # Display current students with enhanced table
                try:
                    students = run_query(f"SELECT * FROM hackathon_2025_class_members WHERE class_id = {selected_class['id']} AND is_active = 1")

                    if len(students) > 0:
                        st.markdown("#### Current Students")
                        
                        # Initialize session state for student selection
                        if 'students_to_remove' not in st.session_state:
                            st.session_state.students_to_remove = set()

                        with st.form(key=f"remove_students_form_{selected_class['id']}"):
                            # Create a styled table
                            table_html = """
                            <div style="overflow-x: auto; margin-bottom: 1rem;">
                                <table style="width: 100%; border-collapse: collapse;">
                                    <thead>
                                        <tr style="border-bottom: 2px solid var(--iq-gray-200);">
                                            <th style="padding: 1rem; text-align: left; font-weight: 700; color: var(--iq-gray-700);">Select</th>
                                            <th style="padding: 1rem; text-align: left; font-weight: 700; color: var(--iq-gray-700);">Email</th>
                                            <th style="padding: 1rem; text-align: left; font-weight: 700; color: var(--iq-gray-700);">Status</th>
                                            <th style="padding: 1rem; text-align: left; font-weight: 700; color: var(--iq-gray-700);">Joined</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                            """
                            st.markdown(table_html, unsafe_allow_html=True)
                            
                            # Student rows with checkboxes
                            students_to_remove = []
                            for _, student in students.iterrows():
                                col1, col2, col3, col4 = st.columns([1, 3, 1, 1])

                                with col1:
                                    if st.checkbox("", key=f"remove_checkbox_{student['id']}", label_visibility="collapsed"):
                                        students_to_remove.append(student['id'])

                                with col2:
                                    st.write(f"📧 {student['email']}")

                                with col3:
                                    status = "Joined" if student.get('joined_at') else "Invited"
                                    if status == "Joined":
                                        st.markdown('<span class="status-pill status-complete">Joined</span>', unsafe_allow_html=True)
                                    else:
                                        st.markdown('<span class="status-pill status-progress">Invited</span>', unsafe_allow_html=True)

                                with col4:
                                    joined_date = student.get('joined_at')
                                    if joined_date:
                                        st.caption(str(joined_date)[:10])
                                    else:
                                        st.caption("-")

                            st.markdown("</tbody></table></div>", unsafe_allow_html=True)
                            
                            # Action buttons
                            col1, col2, col3 = st.columns([2, 2, 3])
                            with col1:
                                remove_selected = st.form_submit_button(
                                    f"🗑️ Remove Selected ({len(students_to_remove)})",
                                    type="secondary",
                                    disabled=len(students_to_remove) == 0
                                )

                            if remove_selected and students_to_remove:
                                try:
                                    for student_id in students_to_remove:
                                        execute_query(f"UPDATE hackathon_2025_class_members SET is_active = 0 WHERE id = {student_id}")
                                    st.success(f"✅ Successfully removed {len(students_to_remove)} student(s)")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error removing students: {str(e)}")
                    else:
                        empty_state_html = """
                        <div class="empty-state">
                            <div class="empty-state-icon">👥</div>
                            <h4 style="color: var(--iq-gray-700);">No students yet</h4>
                            <p style="color: var(--iq-gray-500);">Add students to your class above</p>
                        </div>
                        """
                        st.markdown(empty_state_html, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ Error loading students: {str(e)}")

            with tab2:
                # View assignments for this class
                st.markdown("### Class Assignments")
                try:
                    assignments = run_query(f"SELECT * FROM hackathon_2025_assignments WHERE class_id = {selected_class['id']} AND is_active = 1 ORDER BY due_date DESC")

                    if len(assignments) > 0:
                        for _, assignment in assignments.iterrows():
                            # Enhanced assignment card
                            assignment_card_html = f"""
                            <div class="glass-card" style="margin-bottom: 1rem;">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <h4 style="margin: 0; color: var(--iq-gray-800); font-weight: 600;">
                                            📚 {assignment['name']}
                                        </h4>
                                        <p style="margin: 0.5rem 0 0 0; color: var(--iq-gray-600);">
                                            Due: {pd.to_datetime(assignment['due_date']).strftime('%B %d, %Y')}
                                        </p>
                                    </div>
                                    <div>
                                        <span class="status-pill status-progress">Active</span>
                                    </div>
                                </div>
                            </div>
                            """
                            st.markdown(assignment_card_html, unsafe_allow_html=True)
                    else:
                        empty_state_html = """
                        <div class="empty-state">
                            <div class="empty-state-icon">📝</div>
                            <h4 style="color: var(--iq-gray-700);">No assignments yet</h4>
                            <p style="color: var(--iq-gray-500);">Create assignments from the Assignments page</p>
                        </div>
                        """
                        st.markdown(empty_state_html, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ Error loading assignments: {str(e)}")

            with tab3:
                st.markdown("### Class Analytics")
                # Add class analytics here
                st.info("📊 Analytics coming soon!")

            # Back button with enhanced styling
            st.markdown("---")
            if st.button("← Back to Classes", type="secondary"):
                st.session_state.manage_class = False
                st.rerun()

        except Exception as e:
            st.error(f"❌ Error in class management: {str(e)}")
            st.session_state.manage_class = False


def show_assignments_page(user):
    st.markdown('<h2 class="main-header">📝 Create Assignment</h2>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color: var(--iq-gray-600); font-size: 1.125rem; margin-bottom: 2rem;">Build custom assignments with Interview Query questions</p>',
        unsafe_allow_html=True)

    # Initialize session state variables
    if 'assignment_name' not in st.session_state:
        st.session_state.assignment_name = ""
    if 'assignment_due_date' not in st.session_state:
        st.session_state.assignment_due_date = datetime.now().date()
    if 'assignment_class_id' not in st.session_state:
        st.session_state.assignment_class_id = None
    if 'assignment_class_name' not in st.session_state:
        st.session_state.assignment_class_name = ""
    if 'selected_questions_dict' not in st.session_state:
        st.session_state.selected_questions_dict = {}
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'last_search_query' not in st.session_state:
        st.session_state.last_search_query = ""
    if 'show_search_results' not in st.session_state:
        st.session_state.show_search_results = False

    # Get user's classes
    try:
        classes = get_classes(user)
        if len(classes) == 0:
            st.warning("Please create a class first!")
            return

        # Enhanced assignment details section
        assignment_card_html = """
        <div class="glass-card" style="margin-bottom: 2rem; background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%); border: 2px solid var(--iq-primary);">
            <h3 style="color: var(--iq-gray-800); font-weight: 600; margin-bottom: 1rem;">📝 Assignment Details</h3>
            <p style="color: var(--iq-gray-600); font-size: 0.875rem; margin-bottom: 1rem;">Fill in these details before searching for questions</p>
        </div>
        """
        st.markdown(assignment_card_html, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            class_options = {row['class_name']: row['id'] for _, row in classes.iterrows()}
            selected_class_name = st.selectbox("Select Class",
                                               list(class_options.keys()),
                                               key="class_select",
                                               help="Choose which class this assignment is for")
            selected_class_id = class_options[selected_class_name]
            st.session_state.assignment_class_id = selected_class_id
            st.session_state.assignment_class_name = selected_class_name

        with col2:
            assignment_name = st.text_input("Assignment Name ⚠️ Required",
                                            value=st.session_state.assignment_name,
                                            placeholder="e.g., Week 3 - Arrays and Strings",
                                            key="assignment_name_input",
                                            help="Give your assignment a descriptive name")
            st.session_state.assignment_name = assignment_name

        with col3:
            due_date = st.date_input("Due Date",
                                     value=st.session_state.assignment_due_date,
                                     min_value=datetime.now().date(),
                                     key="due_date_input",
                                     help="When should students complete this by?")
            st.session_state.assignment_due_date = due_date

        # Show a warning if assignment name is empty
        if not st.session_state.assignment_name:
            st.warning("⚠️ Please enter an assignment name above before proceeding")

        # Enhanced search section
        st.markdown("### 🔍 Search Questions")

        # Use a container to prevent form submission issues
        search_container = st.container()
        with search_container:
            col1, col2 = st.columns([4, 1])

            with col1:
                search_query = st.text_input("Search questions by topic, type, or difficulty",
                                             placeholder="e.g., dynamic programming, arrays, SQL joins",
                                             key="search_input",
                                             value=st.session_state.get('last_search_query', ''))

            with col2:
                st.write("")  # Spacer for alignment
                search_clicked = st.button("🔍 Search", type="primary", use_container_width=True)

        # Search questions when button is clicked or when there's a new search query
        if search_clicked and search_query:
            st.session_state.last_search_query = search_query
            st.session_state.show_search_results = True

            try:
                # Use magus semantic search API
                with st.spinner("Searching for relevant questions..."):
                    url = "https://magus.interviewquery.com/search"
                    payload = {
                        "query": search_query,
                        "content_types": ["questions"],
                        "companies": [],
                        "positions": [],
                        "limit": 20
                    }

                    response = requests.post(url, json=payload, timeout=10)
                    response.raise_for_status()

                    search_data = response.json()
                    results = search_data.get('results', [])

                    questions = []
                    if results:
                        # Get question IDs from search results
                        question_ids = []
                        question_urls = {}
                        for result in results:
                            content_id = result.get('content_id')
                            if content_id:
                                question_ids.append(str(content_id))
                                question_urls[content_id] = result.get('url', '')

                        # Fetch full question details from database
                        if question_ids:
                            ids_str = ','.join(question_ids)
                            questions_sql = f"""
                            SELECT id, title, type, level, summary, body_markdown, slug
                            FROM questions 
                            WHERE id IN ({ids_str})
                            AND is_published = 1
                            """
                            db_results = run_query(questions_sql)

                            if len(db_results) > 0:
                                # Create a mapping to preserve search order
                                id_to_order = {int(qid): idx for idx, qid in enumerate(question_ids)}

                                # Sort results by search relevance
                                sorted_results = db_results.iloc[
                                    db_results['id'].map(lambda x: id_to_order.get(x, 999)).argsort()
                                ]

                                for _, row in sorted_results.iterrows():
                                    questions.append({
                                        'id': row['id'],
                                        'title': row['title'],
                                        'type': row['type'],
                                        'level': row['level'],
                                        'body_markdown': row.get('body_markdown', ''),
                                        'url': question_urls.get(row['id'], '')
                                    })

                    # Store search results in session state
                    st.session_state.search_results = questions

                    if not questions:
                        st.info(f"No questions found for '{search_query}'. Try different keywords.")

            except requests.RequestException as e:
                st.error(f"Error connecting to search service: {str(e)}")
                # Fallback to database search
                try:
                    search_sql = f"""
                    SELECT id, title, type, level, summary, body_markdown
                    FROM questions 
                    WHERE (title LIKE '%{search_query}%' OR body_markdown LIKE '%{search_query}%')
                    AND is_published = 1
                    LIMIT 20
                    """
                    results = run_query(search_sql)

                    questions = []
                    for _, row in results.iterrows():
                        questions.append({
                            'id': row['id'],
                            'title': row['title'],
                            'type': row['type'],
                            'level': row['level'],
                            'body_markdown': row.get('body_markdown', '')
                        })

                    st.session_state.search_results = questions

                except Exception as db_error:
                    st.error(f"Database search error: {str(db_error)}")
                    st.session_state.search_results = []

        # Show default questions only if no search has been performed
        elif not st.session_state.show_search_results and not st.session_state.search_results:
            try:
                default_sql = """
                              SELECT id, title, type, level, body_markdown
                              FROM questions
                              WHERE is_published = 1
                              ORDER BY created_at DESC LIMIT 10 \
                              """
                results = run_query(default_sql)

                questions = []
                for _, row in results.iterrows():
                    questions.append({
                        'id': row['id'],
                        'title': row['title'],
                        'type': row['type'],
                        'level': row['level'],
                        'body_markdown': row['body_markdown']
                    })

                st.session_state.search_results = questions

            except Exception as e:
                st.error(f"Error loading default questions: {str(e)}")
                st.session_state.search_results = []

        # Display search results from session state
        if st.session_state.search_results:
            st.markdown(f"### Found {len(st.session_state.search_results)} Questions")

            # Show current assignment details if set
            if st.session_state.assignment_name:
                st.success(
                    f"✅ Creating assignment: **{st.session_state.assignment_name}** for **{st.session_state.assignment_class_name}** (Due: {st.session_state.assignment_due_date})")
            else:
                st.error(
                    "❌ Please enter an assignment name in the Assignment Details section above before selecting questions!")

            # Display questions with selection tracking
            for i, question in enumerate(st.session_state.search_results):
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                    with col1:
                        st.write(f"**{question['title']}**")

                        # Expandable question body
                        with st.expander("View Question Details"):
                            st.markdown(question.get('body_markdown', 'No content available'))

                    with col2:
                        question_type = question.get('type', 'Unknown')
                        st.caption(f"Type: {question_type}")

                    with col3:
                        level = question.get('level', 1)
                        difficulty_map = {1: '🟢 Easy', 2: '🟡 Medium', 3: '🔴 Hard'}
                        difficulty = difficulty_map.get(level, f"Level {level}")
                        st.write(difficulty)

                    with col4:
                        q_id = question['id']

                        # Check if question is already selected
                        if q_id in st.session_state.selected_questions_dict:
                            if st.button("✓ Selected",
                                         key=f"deselect_{q_id}_{i}",
                                         type="secondary"):
                                del st.session_state.selected_questions_dict[q_id]
                                st.rerun()
                        else:
                            if st.button("Add",
                                         key=f"select_{q_id}_{i}"):
                                print(question)
                                st.session_state.selected_questions_dict[q_id] = {
                                    'id': q_id,
                                    'title': question['title'],
                                    'type': question.get('type', 'Unknown'),
                                    'level': question.get('level', 1),
                                    'url': question.get('url', '')
                                }
                                st.rerun()

                    st.divider()

        # Show selected questions and create button
        if st.session_state.selected_questions_dict:
            st.markdown(f"### 📋 Selected Questions ({len(st.session_state.selected_questions_dict)})")

            # Display selected questions
            for q_id, q_data in list(st.session_state.selected_questions_dict.items()):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    level = q_data.get('level', 1)
                    difficulty_map = {1: '🟢', 2: '🟡', 3: '🔴'}
                    difficulty_icon = difficulty_map.get(level, '⚪')
                    st.write(f"{difficulty_icon} **{q_data['title']}**")
                with col2:
                    st.caption(f"Type: {q_data.get('type', 'Unknown')}")
                with col3:
                    if st.button("Remove", key=f"remove_final_{q_id}"):
                        del st.session_state.selected_questions_dict[q_id]
                        st.rerun()

            st.divider()

            # Create assignment button
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                if st.button("🚀 Create Assignment", type="primary", use_container_width=True,
                             key="create_assignment_button"):
                    # Use values from session state
                    selected_question_ids = list(st.session_state.selected_questions_dict.keys())

                    if st.session_state.assignment_name and selected_question_ids:
                        try:
                            # Insert assignment
                            insert_query = f"""
                            INSERT INTO hackathon_2025_assignments (class_id, name, due_date) 
                            VALUES ({st.session_state.assignment_class_id}, '{st.session_state.assignment_name}', '{st.session_state.assignment_due_date}')
                            """
                            execute_query(insert_query)

                            # Get the assignment ID
                            assignment_result = run_query(f"""
                            SELECT id FROM hackathon_2025_assignments 
                            WHERE class_id = {st.session_state.assignment_class_id} AND name = '{st.session_state.assignment_name}' 
                            ORDER BY created_at DESC LIMIT 1
                            """)

                            if len(assignment_result) > 0:
                                assignment_id = assignment_result.iloc[0]['id']

                                # Show loading indicator
                                with st.spinner("Creating assignment and adding questions..."):
                                    # Insert assignment questions
                                    for q_id in selected_question_ids:
                                        question_query = f"""
                                        INSERT INTO hackathon_2025_assignment_questions (assignment_id, question_id, points) 
                                        VALUES ({assignment_id}, {q_id}, 10)
                                        """
                                        execute_query(question_query)

                                    # Get question details for the assignment
                                    with st.spinner("Fetching question details..."):
                                        questions_query = f"""
                                        SELECT q.id, q.title, q.type, q.level, aq.points
                                        FROM hackathon_2025_assignment_questions aq
                                        JOIN questions q ON aq.question_id = q.id
                                        WHERE aq.assignment_id = {assignment_id}
                                        """
                                        assignment_questions = run_query(questions_query)

                                        # Add URLs from session state
                                        for idx, row in assignment_questions.iterrows():
                                            q_id = row['id']
                                            if q_id in st.session_state.selected_questions_dict:
                                                assignment_questions.at[idx, 'url'] = \
                                                    st.session_state.selected_questions_dict[q_id].get('url', '')

                                    # Get all students in the class
                                    with st.spinner("Loading student roster..."):
                                        students = run_query(f"""
                                        SELECT email FROM hackathon_2025_class_members 
                                        WHERE class_id = {st.session_state.assignment_class_id} AND is_active = 1
                                        """)

                                    # Send emails to all students
                                    if len(students) > 0:
                                        email_count = 0

                                        # Prepare question list with links
                                        question_list = []
                                        for _, q in assignment_questions.iterrows():
                                            # Create signed link for each question
                                            question_url = q.get('url', '')
                                            if question_url:
                                                question_link = create_signed_link(question_url, assignment_id,
                                                                                   "student@university.edu")
                                            else:
                                                # Fallback if no URL
                                                question_link = f"https://www.interviewquery.com/questions/{q['id']}"

                                            question_list.append({
                                                'id': q['id'],
                                                'title': q['title'],
                                                'points': q['points'],
                                                'link': question_link,
                                                'difficulty': {1: 'Easy', 2: 'Medium', 3: 'Hard'}.get(q['level'],
                                                                                                      'Medium')
                                            })

                                        # Send emails with progress bar
                                        progress_bar = st.progress(0, text="Sending emails to students...")

                                        for idx, (_, student) in enumerate(students.iterrows()):
                                            try:
                                                # Update question links for this specific student
                                                student_questions = []
                                                for q in question_list:
                                                    q_url = st.session_state.selected_questions_dict.get(q['id'],
                                                                                                         {}).get(
                                                        'url', '')
                                                    if q_url:
                                                        student_link = create_signed_link(q_url, assignment_id,
                                                                                          student['email'])
                                                    else:
                                                        # Query the questions table for the slug
                                                        slug_query = f"SELECT slug FROM questions WHERE id = {q['id']}"
                                                        slug_result = run_query(slug_query)
                                                        
                                                        if not slug_result.empty and slug_result.iloc[0]['slug']:
                                                            # Use the slug to create proper URL
                                                            q_url = f"https://www.interviewquery.com/questions/{slug_result.iloc[0]['slug']}"
                                                            student_link = create_signed_link(q_url, assignment_id,
                                                                                              student['email'])
                                                        else:
                                                            # Final fallback - use question ID
                                                            student_link = f"https://www.interviewquery.com/questions/{q['id']}"

                                                    student_questions.append({
                                                        'title': q['title'],
                                                        'points': q['points'],
                                                        'link': student_link,
                                                        'difficulty': q['difficulty']
                                                    })

                                                subject = f"📚 New Assignment: {st.session_state.assignment_name}"
                                                html_body = get_assignment_notification_template(
                                                    assignment_name=st.session_state.assignment_name,
                                                    class_name=st.session_state.assignment_class_name,
                                                    due_date=str(st.session_state.assignment_due_date),
                                                    question_count=len(selected_question_ids),
                                                    student_email=student['email'],
                                                    questions=student_questions
                                                )
                                                send_email("noreply@interviewquery.com", student['email'], subject,
                                                           html_body)
                                                email_count += 1

                                                # Update progress
                                                progress = (idx + 1) / len(students)
                                                progress_bar.progress(progress,
                                                                      text=f"Sent {email_count}/{len(students)} emails...")

                                            except Exception as email_error:
                                                st.warning(
                                                    f"Failed to send email to {student['email']}: {str(email_error)}")

                                        st.success(
                                            f"Assignment '{st.session_state.assignment_name}' created with {len(selected_question_ids)} questions! Notified {email_count} students.")
                                    else:
                                        st.success(
                                            f"Assignment '{st.session_state.assignment_name}' created with {len(selected_question_ids)} questions!")

                                    # Clear selections and reset state
                                    st.session_state.selected_questions_dict = {}
                                    st.session_state.assignment_name = ""
                                    st.session_state.assignment_due_date = datetime.now().date()
                                    st.session_state.assignment_class_id = None
                                    st.session_state.assignment_class_name = ""
                                    st.session_state.search_results = []
                                    st.session_state.last_search_query = ""
                                    st.session_state.show_search_results = False

                                    st.rerun()

                        except Exception as e:
                            st.error(f"Error creating assignment: {str(e)}")
                    else:
                        st.error("Please enter assignment name and select at least one question.")

            with col2:
                st.info(f"{len(st.session_state.selected_questions_dict)} questions")

            with col3:
                if st.button("Clear All", key="clear_all_questions"):
                    st.session_state.selected_questions_dict = {}
                    st.rerun()

        elif st.session_state.last_search_query:
            st.info("No questions found. Try a different search term.")

    except Exception as e:
        st.error(f"Error loading assignments page: {str(e)}")

def show_progress_page(user):
    st.markdown('<h2 class="main-header">📊 Student Progress Tracking</h2>', unsafe_allow_html=True)
    st.markdown('<p style="color: var(--iq-gray-600); font-size: 1.125rem; margin-bottom: 2rem;">Monitor student performance and track assignment completion</p>', unsafe_allow_html=True)

    # Get user's classes
    try:
        classes = get_classes(user)
        if len(classes) == 0:
            st.warning("No classes found. Create a class first!")
            return

        # Class selection
        class_options = {row['class_name']: row['id'] for _, row in classes.iterrows()}
        selected_class_name = st.selectbox("Select Class", list(class_options.keys()))
        selected_class_id = class_options[selected_class_name]

        # Get assignments for selected class
        assignments_query = f"""
        SELECT a.*, 
               (SELECT COUNT(DISTINCT aq.question_id) 
                FROM hackathon_2025_assignment_questions aq 
                WHERE aq.assignment_id = a.id) as question_count
        FROM hackathon_2025_assignments a
        WHERE a.class_id = {selected_class_id} 
        AND a.is_active = 1
        ORDER BY a.due_date DESC
        """
        assignments = run_query(assignments_query)

        if len(assignments) == 0:
            st.info("No assignments found for this class.")
            return

        # Assignment selection
        assignment_options = {f"{row['name']} (Due: {row['due_date']})" : row['id']
                            for _, row in assignments.iterrows()}
        selected_assignment_display = st.selectbox("Select Assignment", list(assignment_options.keys()))
        selected_assignment_id = assignment_options[selected_assignment_display]

        # Get assignment details
        assignment = assignments[assignments['id'] == selected_assignment_id].iloc[0]

        # Display assignment info
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Assignment", assignment['name'])
        with col2:
            st.metric("Due Date", str(assignment['due_date'])[:10])
        with col3:
            st.metric("Questions", assignment['question_count'])
        with col4:
            days_left = (pd.to_datetime(assignment['due_date']) - pd.Timestamp.now()).days
            st.metric("Days Left", max(0, days_left))

        st.divider()

        # Get student progress data
        # Get student progress data
        progress_query = f"""
                WITH assignment_questions AS (
                    SELECT question_id, points
                    FROM hackathon_2025_assignment_questions
                    WHERE assignment_id = {selected_assignment_id}
                ),
                -- Step 2: Get students in the class (via assignment → class → members → users)
                class_students AS (
                    SELECT
                        cm.email,
                        u.id as user_id,
                        u.first_name,
                        u.last_name,
                        u.created_at as joined_at
                    FROM hackathon_2025_assignments a
                    JOIN hackathon_2025_class_members cm ON a.class_id = cm.class_id
                    JOIN users u ON cm.email = u.email
                    WHERE a.id = {selected_assignment_id}
                        AND cm.is_active = 1
                )
                -- Step 3: For each (student, question) pair, check completion
                SELECT
                    cs.email,
                    cs.user_id,
                    cs.joined_at,
                    CONCAT(COALESCE(cs.first_name, ''), ' ', COALESCE(cs.last_name, '')) as student_name,
                    COUNT(aq.question_id) as total_questions,
                    SUM(
                        CASE
                            WHEN q.type IN ('sql', 'python', 'algorithms') THEN
                                CASE WHEN EXISTS (
                                    SELECT 1 FROM user_code_runs ucr
                                    WHERE ucr.user_id = cs.user_id
                                    AND ucr.question_id = aq.question_id
                                    AND ucr.is_accepted = 1
                                    AND ucr.created_at >= '{assignment['created_at']}'
                                ) THEN 1 ELSE 0 END
                            ELSE
                                CASE WHEN EXISTS (
                                    SELECT 1 FROM text_submissions ts
                                    WHERE ts.user_id = cs.user_id
                                    AND ts.question_id = aq.question_id
                                    AND ts.score >= 8
                                    AND ts.created_at >= '{assignment['created_at']}'
                                ) THEN 1 ELSE 0 END
                        END
                    ) as completed_questions,
                    SUM(
                        CASE
                            WHEN q.type IN ('sql', 'python', 'algorithms') THEN
                                CASE WHEN EXISTS (
                                    SELECT 1 FROM user_code_runs ucr
                                    WHERE ucr.user_id = cs.user_id
                                    AND ucr.question_id = aq.question_id
                                    AND ucr.is_accepted = 1
                                    AND ucr.created_at >= '{assignment['created_at']}'
                                ) THEN aq.points ELSE 0 END
                            ELSE
                                CASE WHEN EXISTS (
                                    SELECT 1 FROM text_submissions ts
                                    WHERE ts.user_id = cs.user_id
                                    AND ts.question_id = aq.question_id
                                    AND ts.score >= 8
                                    AND ts.created_at >= '{assignment['created_at']}'
                                ) THEN aq.points ELSE 0 END
                        END
                    ) as points_earned,
                    SUM(aq.points) as total_points
                FROM class_students cs
                CROSS JOIN assignment_questions aq
                JOIN questions q ON q.id = aq.question_id
                GROUP BY cs.email, cs.user_id, cs.joined_at, cs.first_name, cs.last_name
                ORDER BY completed_questions DESC, cs.email
                """
        try:
            progress_data = run_query(progress_query)

            if len(progress_data) > 0:
                # Summary metrics
                st.markdown("### 📈 Class Overview")

                total_students = len(progress_data)
                students_started = len(progress_data[progress_data['completed_questions'] > 0])
                students_completed = len(progress_data[progress_data['completed_questions'] == progress_data['total_questions']])
                avg_completion = progress_data['completed_questions'].sum() / (progress_data['total_questions'].sum() or 1) * 100

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Students", total_students)
                with col2:
                    st.metric("Started", f"{students_started} ({students_started/total_students*100:.0f}%)")
                with col3:
                    st.metric("Completed", f"{students_completed} ({students_completed/total_students*100:.0f}%)")
                with col4:
                    st.metric("Avg Progress", f"{avg_completion:.0f}%")

                st.divider()

                # Question completion summary
                st.markdown("### 📝 Question Completion Overview")

                # Initialize question_stats variable
                question_stats = pd.DataFrame()

                # Get question completion stats
                # Get question completion stats
                question_stats_query = f"""
                                SELECT 
                                    q.title as question_title,
                                    q.type as question_type,
                                    q.level as difficulty,
                                    aq.points,
                                    COUNT(DISTINCT u.id) as total_students,
                                    COUNT(DISTINCT CASE 
                                        WHEN q.type IN ('sql', 'python', 'algorithms') AND ucr.is_accepted = 1 THEN u.id
                                        WHEN q.type NOT IN ('sql', 'python', 'algorithms') AND ts.score >= 8 THEN u.id
                                    END) as students_completed,
                                    COUNT(DISTINCT CASE 
                                        WHEN q.type IN ('sql', 'python', 'algorithms') AND ucr.is_submitted = 1 AND ucr.is_accepted = 0 THEN u.id
                                        WHEN q.type NOT IN ('sql', 'python', 'algorithms') AND ts.score > 0 AND ts.score < 8 THEN u.id
                                    END) as students_attempted
                                FROM hackathon_2025_assignment_questions aq
                                JOIN questions q ON aq.question_id = q.id
                                CROSS JOIN hackathon_2025_class_members cm
                                INNER JOIN users u ON cm.email = u.email
                                LEFT JOIN user_code_runs ucr ON ucr.user_id = u.id
                                    AND ucr.question_id = aq.question_id
                                    AND ucr.created_at >= '{assignment['created_at']}'
                                    AND ucr.is_submitted = 1
                                LEFT JOIN text_submissions ts ON ts.user_id = u.id
                                    AND ts.question_id = aq.question_id
                                    AND ts.created_at >= '{assignment['created_at']}'
                                WHERE aq.assignment_id = {selected_assignment_id}
                                    AND cm.class_id = {selected_class_id}
                                    AND cm.is_active = 1
                                GROUP BY q.id, q.title, q.type, q.level, aq.points
                                ORDER BY q.title
                                """

                try:
                    question_stats = run_query(question_stats_query)

                    if len(question_stats) > 0:
                        for _, q in question_stats.iterrows():
                            with st.container():
                                q_col1, q_col2, q_col3, q_col4, q_col5 = st.columns([3, 1, 1, 2, 1])

                                with q_col1:
                                    st.write(f"**{q['question_title']}**")
                                    st.caption(f"Type: {q['question_type']} | {q['points']} points")

                                with q_col2:
                                    difficulty_map = {1: '🟢 Easy', 2: '🟡 Medium', 3: '🔴 Hard'}
                                    st.write(difficulty_map.get(q['difficulty'], 'Unknown'))

                                with q_col3:
                                    completion_rate = (q['students_completed'] / q['total_students'] * 100) if q['total_students'] > 0 else 0
                                    st.metric("Completed", f"{q['students_completed']}/{q['total_students']}")

                                with q_col4:
                                    # Custom progress bar with Interview Query styling
                                    progress_html = f"""
                                    <div class="progress-container">
                                        <div class="progress-fill" style="width: {completion_rate:.0f}%;"></div>
                                    </div>
                                    <small style="color: var(--iq-gray-600); font-weight: 500;">{completion_rate:.0f}% completion rate</small>
                                    """
                                    st.markdown(progress_html, unsafe_allow_html=True)

                                with q_col5:
                                    if q['students_attempted'] > 0:
                                        st.caption(f"🔄 {q['students_attempted']} attempting")

                            st.divider()

                except Exception as e:
                    st.error(f"Error loading question statistics: {str(e)}")

                st.divider()

                # Individual student progress
                st.markdown("### 👥 Individual Progress")

                # Add progress bar column
                progress_data['progress_pct'] = (progress_data['completed_questions'] / progress_data['total_questions'] * 100).fillna(0)
                progress_data['status'] = progress_data.apply(
                    lambda x: '✅ Complete' if x['progress_pct'] == 100
                    else '🟡 In Progress' if x['progress_pct'] > 0
                    else '⚪ Not Started', axis=1
                )

                # Display options
                col1, col2 = st.columns([1, 3])
                with col1:
                    show_only_active = st.checkbox("Show only active students", value=True)

                # Filter data
                display_data = progress_data
                if show_only_active:
                    display_data = progress_data[progress_data['completed_questions'] > 0]

                # Display student progress
                for _, student in display_data.iterrows():
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 2, 1])

                        with col1:
                            student_name = student['student_name'].strip() if student['student_name'] else ""
                            if not student_name or student_name == " ":
                                student_name = student['email']
                            st.write(f"**{student_name}**")
                            st.caption(student['email'])

                        with col2:
                            # Map status to CSS class
                            status_class_map = {
                                '✅ Complete': 'status-complete',
                                '🟡 In Progress': 'status-progress',
                                '⚪ Not Started': 'status-notstarted'
                            }
                            status_class = status_class_map.get(student['status'], 'status-notstarted')
                            status_text = student['status'].replace('✅ ', '').replace('🟡 ', '').replace('⚪ ', '')

                            status_html = f'<span class="status-pill {status_class}">{status_text}</span>'
                            st.markdown(status_html, unsafe_allow_html=True)

                        with col3:
                            st.write(f"{student['completed_questions']}/{student['total_questions']} done")

                        with col4:
                            # Custom progress bar with Interview Query styling
                            progress_html = f"""
                            <div class="progress-container">
                                <div class="progress-fill" style="width: {student['progress_pct']:.0f}%;"></div>
                            </div>
                            <small style="color: var(--iq-gray-600); font-weight: 500;">{student['progress_pct']:.0f}%</small>
                            """
                            st.markdown(progress_html, unsafe_allow_html=True)

                        with col5:
                            if student['total_points'] > 0:
                                st.write(f"🏆 {student['points_earned']}/{student['total_points']}")

                        # Expandable section to show individual question status
                        with st.expander("View Question Details"):
                            # Get detailed question status for this student
                            question_detail_query = f"""
                            SELECT 
                                q.title as question_title,
                                q.type as question_type,
                                q.level as difficulty,
                                aq.points,
                                CASE 
                                    WHEN q.type IN ('sql', 'python', 'algorithms') THEN
                                        CASE
                                            WHEN ucr.is_accepted = 1 THEN 'Completed'
                                            WHEN ucr.is_submitted = 1 THEN 'Attempted'
                                            ELSE 'Not Started'
                                        END
                                    ELSE
                                        CASE
                                            WHEN ts.score >= 7 THEN 'Completed'
                                            WHEN ts.score > 0 THEN 'Attempted'
                                            ELSE 'Not Started'
                                        END
                                END as status,
                                CASE
                                    WHEN q.type IN ('sql', 'python', 'algorithms') THEN ucr.is_accepted
                                    ELSE ts.score
                                END as score,
                                COALESCE(ucr.created_at, ts.created_at) as last_submission
                            FROM hackathon_2025_assignment_questions aq
                            JOIN questions q ON aq.question_id = q.id
                            LEFT JOIN (
                                SELECT user_id, question_id, MAX(is_accepted) as is_accepted, MAX(is_submitted) as is_submitted, MAX(created_at) as created_at
                                FROM user_code_runs
                                GROUP BY user_id, question_id
                            ) ucr ON ucr.user_id = {student['user_id'] if student['user_id'] else 'NULL'}
                                AND ucr.question_id = aq.question_id
                                AND ucr.created_at >= '{assignment['created_at']}'
                            LEFT JOIN (
                                SELECT user_id, question_id, MAX(score) as score, MAX(created_at) as created_at
                                FROM text_submissions
                                GROUP BY user_id, question_id
                            ) ts ON ts.user_id = {student['user_id'] if student['user_id'] else 'NULL'}
                                AND ts.question_id = aq.question_id
                                AND ts.created_at >= '{assignment['created_at']}'
                            WHERE aq.assignment_id = {selected_assignment_id}
                            ORDER BY q.title
                            """

                            try:
                                question_details = run_query(question_detail_query)

                                if len(question_details) > 0:
                                    # Create columns for question details
                                    for _, q in question_details.iterrows():
                                        q_col1, q_col2, q_col3, q_col4 = st.columns([3, 1, 1, 1])

                                        with q_col1:
                                            st.write(f"📝 {q['question_title']}")

                                        with q_col2:
                                            difficulty_map = {1: '🟢 Easy', 2: '🟡 Medium', 3: '🔴 Hard'}
                                            st.write(difficulty_map.get(q['difficulty'], 'Unknown'))

                                        with q_col3:
                                            status_emoji = {
                                                'Completed': '✅',
                                                'Attempted': '🔄',
                                                'Text Submitted': '📝',
                                                'Not Started': '⚪'
                                            }
                                            # Display status with score if available
                                            status_display = f"{status_emoji.get(q['status'], '')} {q['status']}"
                                            
                                            # Add score information
                                            if q['score'] is not None:
                                                if q['question_type'] in ['sql', 'python', 'algorithms']:
                                                    # For coding questions, show checkmark or X
                                                    if q['score'] == 1:
                                                        status_display += " ✓"
                                                else:
                                                    # For text questions, show percentage score
                                                    status_display += f" ({q['score']*100:.0f}%)"
                                            
                                            st.write(status_display)

                                        with q_col4:
                                            if q['last_submission']:
                                                st.caption(f"Last: {pd.to_datetime(q['last_submission']).strftime('%m/%d %I:%M %p')}")
                                            else:
                                                st.caption("No submission")

                                else:
                                    st.info("No questions found for this assignment")

                            except Exception as e:
                                st.error(f"Error loading question details: {str(e)}")

                        st.divider()

                # Export options
                st.markdown("### 📤 Export Options")

                col1, col2, col3 = st.columns(3)

                with col1:
                    # CSV export with detailed question breakdown
                    export_query = f"""
                    SELECT 
                        cm.email,
                        CONCAT(COALESCE(u.first_name, ''), ' ', COALESCE(u.last_name, '')) as student_name,
                        q.title as question_title,
                        q.type as question_type,
                        q.level as difficulty,
                        aq.points,
                        CASE 
                            WHEN ucr.is_accepted = 1 THEN 'Completed'
                            WHEN ucr.is_submitted = 1 THEN 'Attempted'
                            WHEN ts.id IS NOT NULL THEN 'Text Submitted'
                            ELSE 'Not Started'
                        END as status,
                        COALESCE(ucr.created_at, ts.created_at) as submission_time
                    FROM hackathon_2025_class_members cm
                    LEFT JOIN users u ON cm.user_id = u.id
                    CROSS JOIN hackathon_2025_assignment_questions aq
                    JOIN questions q ON aq.question_id = q.id
                    LEFT JOIN user_code_runs ucr ON ucr.user_id = cm.user_id
                        AND ucr.question_id = aq.question_id
                        AND ucr.created_at >= '{assignment['created_at']}'
                        AND ucr.is_submitted = 1
                    LEFT JOIN text_submissions ts ON ts.user_id = cm.user_id
                        AND ts.question_id = aq.question_id
                        AND ts.created_at >= '{assignment['created_at']}'
                    WHERE cm.class_id = {selected_class_id}
                        AND cm.is_active = 1
                        AND aq.assignment_id = {selected_assignment_id}
                    ORDER BY cm.email, q.title
                    """

                    try:
                        export_data = run_query(export_query)
                        csv = export_data.to_csv(index=False)
                        st.download_button(
                            label="📊 Download Detailed CSV",
                            data=csv,
                            file_name=f"{assignment['name']}_detailed_progress_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                    except Exception as e:
                        # Fallback to simple export
                        csv = progress_data.to_csv(index=False)
                        st.download_button(
                            label="📊 Download CSV",
                            data=csv,
                            file_name=f"{assignment['name']}_progress_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )

                with col2:
                    if st.button("📧 Email Progress Reports"):
                        with st.spinner("Sending progress reports..."):
                            email_count = 0
                            email_errors = 0

                            for _, student in progress_data.iterrows():
                                try:
                                    # Get detailed question status for this student
                                    student_detail_query = f"""
                                    SELECT 
                                        q.title as question_title,
                                        CASE 
                                            WHEN ucr.is_accepted = 1 THEN 'Completed'
                                            WHEN ucr.is_submitted = 1 THEN 'Attempted'
                                            WHEN ts.id IS NOT NULL THEN 'Text Submitted'
                                            ELSE 'Not Started'
                                        END as status
                                    FROM hackathon_2025_assignment_questions aq
                                    JOIN questions q ON aq.question_id = q.id
                                    LEFT JOIN user_code_runs ucr ON ucr.user_id = {student['user_id'] if student['user_id'] else 'NULL'}
                                        AND ucr.question_id = aq.question_id
                                        AND ucr.created_at >= '{assignment['created_at']}'
                                        AND ucr.is_submitted = 1
                                    LEFT JOIN text_submissions ts ON ts.user_id = {student['user_id'] if student['user_id'] else 'NULL'}
                                        AND ts.question_id = aq.question_id
                                        AND ts.created_at >= '{assignment['created_at']}'
                                    WHERE aq.assignment_id = {selected_assignment_id}
                                    ORDER BY q.title
                                    """

                                    student_questions = run_query(student_detail_query)

                                    # Create email content
                                    questions_html = ""
                                    for _, q in student_questions.iterrows():
                                        status_color = {
                                            'Completed': '#10b981',
                                            'Attempted': '#f59e0b',
                                            'Text Submitted': '#3b82f6',
                                            'Not Started': '#6b7280'
                                        }.get(q['status'], '#6b7280')

                                        questions_html += f"""
                                        <tr>
                                            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb;">{q['question_title']}</td>
                                            <td style="padding: 8px; border-bottom: 1px solid #e5e7eb; color: {status_color}; font-weight: 600;">{q['status']}</td>
                                        </tr>
                                        """

                                    # Create progress report email
                                    subject = f"Progress Report: {assignment['name']} - {selected_class_name}"

                                    student_name = student['student_name'].strip() if student['student_name'] and student['student_name'].strip() else student['email']

                                    html_body = f"""
                                    <!DOCTYPE html>
                                    <html>
                                    <head>
                                        <style>
                                            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                                            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                                            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                                            .content {{ background: #f7fafc; padding: 20px; border-radius: 0 0 8px 8px; }}
                                            .progress-bar {{ background: #e5e7eb; border-radius: 4px; height: 20px; margin: 10px 0; }}
                                            .progress-fill {{ background: #667eea; height: 100%; border-radius: 4px; transition: width 0.3s; }}
                                            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                                            th {{ background: #f3f4f6; padding: 10px; text-align: left; }}
                                        </style>
                                    </head>
                                    <body>
                                        <div class="container">
                                            <div class="header">
                                                <h2>Progress Report: {assignment['name']}</h2>
                                                <p>Class: {selected_class_name}</p>
                                            </div>
                                            <div class="content">
                                                <p>Hi {student_name},</p>
                                                <p>Here's your current progress on the assignment:</p>
                                                
                                                <h3>Overall Progress</h3>
                                                <div class="progress-bar">
                                                    <div class="progress-fill" style="width: {student['progress_pct']:.0f}%;"></div>
                                                </div>
                                                <p><strong>{student['completed_questions']}/{student['total_questions']}</strong> questions completed ({student['progress_pct']:.0f}%)</p>
                                                
                                                <h3>Question Status</h3>
                                                <table>
                                                    <tr>
                                                        <th>Question</th>
                                                        <th>Status</th>
                                                    </tr>
                                                    {questions_html}
                                                </table>
                                                
                                                <p>Due Date: <strong>{assignment['due_date']}</strong></p>
                                                
                                                <p>Keep up the good work!</p>
                                                
                                                <p>Best regards,<br>Your Instructor</p>
                                            </div>
                                        </div>
                                    </body>
                                    </html>
                                    """

                                    # Send email
                                    send_email(
                                        from_email="noreply@interviewquery.com",
                                        to_email=student['email'],
                                        subject=subject,
                                        html_body=html_body
                                    )
                                    email_count += 1

                                except Exception as e:
                                    email_errors += 1
                                    st.error(f"Failed to send to {student['email']}: {str(e)}")

                            if email_errors == 0:
                                st.success(f"✅ Successfully sent {email_count} progress reports!")
                            else:
                                st.warning(f"Sent {email_count} reports with {email_errors} errors.")

                with col3:
                    if st.button("📈 Generate Analytics"):
                        # Show analytics in an expandable section
                        with st.expander("📊 Assignment Analytics", expanded=True):
                            # Create visualizations

                            # 1. Completion rate by student
                            fig1 = px.bar(
                                progress_data.sort_values('progress_pct', ascending=True),
                                x='progress_pct',
                                y='email',
                                orientation='h',
                                title='Student Completion Rates',
                                labels={'progress_pct': 'Completion %', 'email': 'Student'},
                                color='progress_pct',
                                color_continuous_scale='viridis'
                            )
                            fig1.update_layout(height=400)
                            st.plotly_chart(fig1, use_container_width=True)

                            # 2. Question difficulty vs completion
                            if 'question_stats' in locals() and len(question_stats) > 0:
                                fig2 = go.Figure()

                                colors = {1: 'green', 2: 'yellow', 3: 'red'}
                                difficulty_names = {1: 'Easy', 2: 'Medium', 3: 'Hard'}

                                for difficulty in [1, 2, 3]:
                                    df_filtered = question_stats[question_stats['difficulty'] == difficulty]
                                    if len(df_filtered) > 0:
                                        completion_rates = (df_filtered['students_completed'] / df_filtered['total_students'] * 100)
                                        fig2.add_trace(go.Bar(
                                            name=difficulty_names[difficulty],
                                            x=df_filtered['question_title'],
                                            y=completion_rates,
                                            marker_color=colors.get(difficulty, 'gray')
                                        ))

                                fig2.update_layout(
                                    title='Question Completion by Difficulty',
                                    xaxis_title='Question',
                                    yaxis_title='Completion Rate (%)',
                                    barmode='group',
                                    height=400
                                )
                                st.plotly_chart(fig2, use_container_width=True)

                            # 3. Summary statistics
                            col_a, col_b = st.columns(2)

                            with col_a:
                                st.metric("Class Average", f"{avg_completion:.1f}%")
                                st.metric("Median Completion", f"{progress_data['progress_pct'].median():.1f}%")

                            with col_b:
                                time_remaining = (pd.to_datetime(assignment['due_date']) - pd.Timestamp.now()).days
                                st.metric("Days Until Due", max(0, time_remaining))

                                # Estimate completion rate
                                if time_remaining > 0 and avg_completion < 100:
                                    days_since_assigned = (pd.Timestamp.now() - pd.to_datetime(assignment['created_at'])).days
                                    if days_since_assigned > 0:
                                        daily_rate = avg_completion / days_since_assigned
                                        projected_completion = min(100, avg_completion + (daily_rate * time_remaining))
                                        st.metric("Projected Completion", f"{projected_completion:.1f}%")

                            # 4. Distribution chart
                            completion_bins = pd.cut(progress_data['progress_pct'],
                                                   bins=[0, 25, 50, 75, 100],
                                                   labels=['0-25%', '26-50%', '51-75%', '76-100%'])
                            bin_counts = completion_bins.value_counts()

                            fig3 = px.pie(
                                values=bin_counts.values,
                                names=bin_counts.index,
                                title='Student Progress Distribution'
                            )
                            st.plotly_chart(fig3, use_container_width=True)

            else:
                st.warning("No student data found for this assignment.")

        except Exception as e:
            st.error(f"Error loading progress data: {str(e)}")

    except Exception as e:
        st.error(f"Error loading progress page: {str(e)}")

def show_dashboard(user):
    # Header
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.markdown('<h1 class="main-header">Interview Query Homework Dashboard</h1>', unsafe_allow_html=True)
    with col2:
        st.write(f"Welcome, {user.email}")
    with col3:
        if st.button("Logout"):
            del st.session_state["user"]
            st.rerun()

    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Select Page",
        ["Classes", "Assignments", "Progress"]
    )

    if page == "Classes":
        show_classes_page(user)
    elif page == "Assignments":
        show_assignments_page(user)
    elif page == "Progress":
        show_progress_page(user)

def main():
    st.title("Interview Query Homeworks")
    st.text("Assign, monitor, and analyze the homeworks of your students.")

    if st.session_state.get("user") is None:
        with st.form(key="get_prof_form"):
            email = st.text_input(label="Please enter your university email")
            submitted = st.form_submit_button("Submit Email")
            if not submitted:
                return
            with st.spinner():
                user = get_users([email])
            if len(user) == 0:
                st.warning("Please use a valid instructor email!")
            else:
                st.session_state["user"] = user.iloc[0]
                st.rerun()
    else:
        show_dashboard(st.session_state["user"])

if __name__ == "__main__":
    main()