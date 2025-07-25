import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Homeworks - Strategic Deep Dive",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .highlight-box {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #1976d2;
        margin: 10px 0;
    }
    .success-box {
        background-color: #e8f5e9;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #4caf50;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3e0;
        padding: 15px;
        border-radius: 8px;
        border-left: 4px solid #ff9800;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("📚 Homeworks Strategic Deck")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigate to:",
    ["Executive Summary", "Adoption Analysis", "Revenue Impact", "Strategic Alignment", "Implementation Roadmap"]
)

# University data
university_data = pd.DataFrame({
    'University': ['UCLA MSBA', 'Purdue University', 'Pace University', 'University of Maryland', 
                   'University of Denver', 'Stony Brook University', 'Carnegie Mellon University',
                   'University of Akron', 'The New School', 'University of Nebraska',
                   'Oklahoma State', 'Georgia Tech', 'University of Georgia', 'Duke University',
                   'Santa Clara University'],
    'Adoption_Rate': [96.36, 90.91, 83.33, 62.75, 51.43, 50.00, 45.65, 
                      38.10, 35.00, 29.41, 19.09, 16.84, 15.09, 7.14, 6.93],
    'Contract_Value': [8000, 7500, 7000, 6500, 6000, 6000, 6500,
                       5500, 5500, 5000, 5000, 5500, 5000, 6000, 5000],
    'Risk_Level': ['Low', 'Low', 'Low', 'Medium', 'Medium', 'Medium', 'High',
                   'High', 'High', 'High', 'High', 'High', 'High', 'High', 'High']
})

# Main content based on navigation
if page == "Executive Summary":
    st.title("🎯 Homeworks: Unlocking B2U Growth Through Adoption")
    
    st.markdown("### The Opportunity")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Current ARR", "$114K", help="Annual Recurring Revenue from 19 university contracts")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Median Adoption", "32.5%", delta="-17.5%", delta_color="inverse", help="Current median student adoption rate")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("At-Risk Revenue", "$66K", help="Revenue from contracts with <50% adoption")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Projected Growth", "+$60K", delta="+52%", help="Conservative estimate with Homeworks")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🔑 Key Insights")
        
        st.markdown('<div class="highlight-box">', unsafe_allow_html=True)
        st.markdown("""
        **The Core Problem**: 11 of 17 universities have adoption rates below 50%, putting $66K in renewal revenue at risk.
        
        **The Solution**: Homeworks enables instructors to assign Interview Query content as graded homework, 
        driving engagement through curriculum integration.
        
        **The Impact**: Conservative projections show +30% renewal improvement and +30% contract value increase.
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("### 🎯 Strategic Value Proposition")
        st.markdown("""
        1. **Immediate Implementation** - No technical barriers, ready to deploy
        2. **Proven Success Pattern** - Top performers (UCLA, Purdue) achieve 90%+ adoption
        3. **Clear ROI** - $60K+ incremental ARR with minimal investment
        4. **Scalable Solution** - Addresses systematic adoption challenges across all contracts
        """)
    
    with col2:
        st.markdown("### 📊 Quick Stats")
        
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = 32.5,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Current Adoption %"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 25], 'color': "lightgray"},
                    {'range': [25, 50], 'color': "gray"}],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90}}))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown("""
        **Success Benchmark**  
        Top universities achieve 90%+ adoption through instructor engagement
        """)
        st.markdown('</div>', unsafe_allow_html=True)

elif page == "Adoption Analysis":
    st.title("📈 Adoption Analysis: The Growth Unlock")
    
    st.markdown("### Current Adoption Landscape")
    
    # Create adoption visualization
    fig = px.bar(university_data.sort_values('Adoption_Rate', ascending=True), 
                 x='Adoption_Rate', 
                 y='University',
                 color='Risk_Level',
                 color_discrete_map={'Low': '#4caf50', 'Medium': '#ff9800', 'High': '#f44336'},
                 title='Student Adoption Rates by University',
                 labels={'Adoption_Rate': 'Adoption Rate (%)', 'University': ''})
    
    fig.add_vline(x=50, line_dash="dash", line_color="gray", annotation_text="50% Threshold")
    fig.update_layout(height=600, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔍 Key Findings")
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown("""
        **Critical Risk**: 65% of universities fall below 50% adoption
        
        - **High Risk**: 11 universities (<40% adoption)
        - **Revenue at Risk**: $66,000 annually
        - **Median Adoption**: 32.5% (vs. 90%+ achievable)
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Risk distribution pie chart
        risk_counts = university_data['Risk_Level'].value_counts()
        fig_pie = px.pie(values=risk_counts.values, 
                         names=risk_counts.index,
                         title='Risk Distribution of Contracts',
                         color_discrete_map={'Low': '#4caf50', 'Medium': '#ff9800', 'High': '#f44336'})
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.markdown("### 💡 Success Patterns")
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown("""
        **What High Adopters Do Differently:**
        
        1. **Instructor Onboarding** - Personal licenses and training
        2. **Curriculum Integration** - Content assigned as homework
        3. **Progress Tracking** - Real-time analytics dashboards
        4. **Student Incentives** - Graded assignments drive usage
        """)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Correlation scatter plot
        fig_scatter = px.scatter(university_data, 
                                x='Adoption_Rate', 
                                y='Contract_Value',
                                size='Contract_Value',
                                color='Risk_Level',
                                title='Adoption vs Contract Value Correlation',
                                color_discrete_map={'Low': '#4caf50', 'Medium': '#ff9800', 'High': '#f44336'})
        fig_scatter.update_layout(height=350)
        st.plotly_chart(fig_scatter, use_container_width=True)

elif page == "Revenue Impact":
    st.title("💰 Revenue Impact Calculator")
    
    st.markdown("### Conservative Growth Projections")
    
    # Interactive calculator
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("#### Adjust Assumptions")
        
        renewal_improvement = st.slider("Renewal Rate Improvement", 10, 50, 30, 5, 
                                      help="Expected improvement in renewal rates with Homeworks")
        
        acv_increase = st.slider("Average Contract Value Increase", 10, 50, 30, 5,
                               help="Expected increase in contract value with instructor licenses")
        
        adoption_target = st.slider("Target Adoption Rate", 50, 95, 75, 5,
                                  help="Target adoption rate with Homeworks implementation")
    
    with col2:
        # Calculate projections
        current_arr = 114000
        current_contracts = 19
        current_acv = 6000
        
        # New metrics
        new_renewals = int(current_contracts * (renewal_improvement / 100))
        new_acv = current_acv * (1 + acv_increase / 100)
        incremental_arr = (new_renewals * new_acv) + (current_contracts * (new_acv - current_acv))
        new_total_arr = current_arr + incremental_arr
        
        st.markdown("#### Projected Impact")
        
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        
        with metric_col1:
            st.metric("New ARR", f"${new_total_arr:,.0f}", 
                     delta=f"+${incremental_arr:,.0f}", 
                     delta_color="normal")
        
        with metric_col2:
            st.metric("Additional Contracts", f"+{new_renewals}", 
                     help="From improved renewals")
        
        with metric_col3:
            st.metric("New ACV", f"${new_acv:,.0f}", 
                     delta=f"+${new_acv - current_acv:,.0f}")
        
        # Waterfall chart
        fig_waterfall = go.Figure(go.Waterfall(
            name = "Revenue Impact",
            orientation = "v",
            measure = ["absolute", "relative", "relative", "total"],
            x = ["Current ARR", "Renewal Improvement", "ACV Increase", "New ARR"],
            textposition = "outside",
            text = [f"${current_arr:,.0f}", 
                   f"+${new_renewals * current_acv:,.0f}", 
                   f"+${current_contracts * (new_acv - current_acv):,.0f}", 
                   f"${new_total_arr:,.0f}"],
            y = [current_arr, 
                new_renewals * current_acv, 
                current_contracts * (new_acv - current_acv), 
                new_total_arr],
            connector = {"line":{"color":"rgb(63, 63, 63)"}},
        ))
        
        fig_waterfall.update_layout(
            title = "Revenue Growth Waterfall",
            showlegend = False,
            height = 400
        )
        st.plotly_chart(fig_waterfall, use_container_width=True)
    
    st.markdown("---")
    
    st.markdown("### 📊 Economic Viability")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("#### Gross Margin")
        st.markdown("# ~80%")
        st.markdown("Strong unit economics")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("#### CAC")
        st.markdown("# $600")
        st.markdown("Efficient acquisition cost")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="metric-card">', unsafe_allow_html=True)
        st.markdown("#### Payback Period")
        st.markdown("# <2 months")
        st.markdown("With improved retention")
        st.markdown('</div>', unsafe_allow_html=True)

elif page == "Strategic Alignment":
    st.title("🎯 Strategic Alignment & Market Opportunity")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### How Homeworks Aligns with IQ's Vision")
        
        st.markdown('<div class="highlight-box">', unsafe_allow_html=True)
        st.markdown("""
        **1. Ecosystem Strengthening**
        - Creates seamless B2U → B2C pipeline
        - Increases brand awareness among students
        - Builds institutional relationships
        
        **2. Product-Market Fit**
        - Addresses explicit instructor needs
        - Solves adoption pain points
        - Creates measurable value
        
        **3. Competitive Moat**
        - First-mover advantage in homework integration
        - Network effects through instructor community
        - Data advantage from engagement analytics
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 🌍 Market Size")
        
        # Market opportunity visualization
        market_data = pd.DataFrame({
            'Segment': ['Current SAM', 'Expanded TAM', 'Global Opportunity'],
            'Value': [30, 150, 500],
            'Description': ['5,000 programs × $6K', '+ Engineering & Business', '+ International Markets']
        })
        
        fig_market = px.funnel(market_data, 
                              y='Segment', 
                              x='Value',
                              title='Market Opportunity ($M)')
        fig_market.update_layout(height=300)
        st.plotly_chart(fig_market, use_container_width=True)
    
    st.markdown("---")
    
    st.markdown("### 🚀 Growth Flywheel")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown("""
        **Step 1: Instructor Adoption**
        - Personal licenses
        - Easy assignment creation
        - Real-time analytics
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown("""
        **Step 2: Student Engagement**
        - Graded homework drives usage
        - Better learning outcomes
        - Higher satisfaction
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown("""
        **Step 3: Revenue Growth**
        - Higher renewal rates
        - Larger contracts
        - Referral generation
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Competitive advantage section
    st.markdown("### 💪 Competitive Advantages")
    
    advantages = {
        "Immediate Deployment": "No technical barriers or platform changes needed",
        "Proven Success Model": "90%+ adoption achieved at top universities",
        "Strong Economics": "80% margins with <2 month payback",
        "First-Mover Position": "No direct competitors in homework integration space",
        "Network Effects": "Each successful implementation drives referrals"
    }
    
    for advantage, description in advantages.items():
        st.markdown(f"**{advantage}**: {description}")

elif page == "Implementation Roadmap":
    st.title("🗺️ Implementation Roadmap")
    
    st.markdown("### Phase 1: Immediate Actions (Month 1)")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="highlight-box">', unsafe_allow_html=True)
        st.markdown("""
        **🎯 Quick Wins**
        1. Launch pilot with 3 low-adoption universities
        2. Create instructor onboarding materials
        3. Develop success metrics dashboard
        4. Build case studies from UCLA/Purdue
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="highlight-box">', unsafe_allow_html=True)
        st.markdown("""
        **👥 Target Universities**
        - Santa Clara University (6.93% adoption)
        - University of Georgia (15.09% adoption)
        - Duke University (7.14% adoption)
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("### Phase 2: Scaling (Months 2-3)")
    
    scaling_tasks = pd.DataFrame({
        'Task': ['Instructor Training Program', 'Analytics Dashboard', 'LMS Integration', 
                 'Success Playbook', 'Referral Program'],
        'Priority': ['High', 'High', 'Medium', 'High', 'Medium'],
        'Impact': ['Direct adoption improvement', 'Value demonstration', 'Reduced friction',
                   'Scalable onboarding', 'Organic growth'],
        'Timeline': ['Week 5-6', 'Week 7-8', 'Week 9-10', 'Week 6-7', 'Week 11-12']
    })
    
    st.dataframe(scaling_tasks, use_container_width=True)
    
    st.markdown("### Phase 3: Optimization (Months 4-6)")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### 📊 Data & Analytics")
        st.markdown("""
        - Predictive adoption models
        - Engagement scoring
        - ROI calculators
        - Benchmarking tools
        """)
    
    with col2:
        st.markdown("#### 🔧 Product Enhancements")
        st.markdown("""
        - AI-powered recommendations
        - Custom assignment builder
        - Peer collaboration features
        - Mobile optimization
        """)
    
    with col3:
        st.markdown("#### 📈 Growth Initiatives")
        st.markdown("""
        - Expansion to new segments
        - International markets
        - Partner integrations
        - Community building
        """)
    
    st.markdown("---")
    
    st.markdown("### 💰 Funding Requirements")
    
    funding_breakdown = pd.DataFrame({
        'Category': ['Strategic Hires', 'Product Development', 'Marketing & Sales', 
                     'Operations', 'Buffer'],
        'Amount': [100000, 75000, 50000, 15000, 10000],
        'Description': ['2 Customer Success Managers', 'Analytics & LMS integration', 
                        'Case studies & collateral', 'Training & support', 'Contingency']
    })
    
    fig_funding = px.pie(funding_breakdown, 
                         values='Amount', 
                         names='Category',
                         title='$250K Seed Funding Allocation')
    st.plotly_chart(fig_funding, use_container_width=True)
    
    st.markdown("### 🎯 Success Metrics & Milestones")
    
    milestones = {
        "Month 1": "3 pilot implementations, 50%+ adoption improvement",
        "Month 3": "10 universities upgraded, $30K incremental ARR",
        "Month 6": "All 19 universities on Homeworks, $100K+ incremental ARR",
        "Month 12": "$600K total ARR, 50+ university contracts"
    }
    
    for milestone, target in milestones.items():
        st.markdown(f"**{milestone}**: {target}")
    
    st.markdown("---")
    
    st.markdown("### 📞 Call to Action")
    
    st.markdown('<div class="success-box">', unsafe_allow_html=True)
    st.markdown("""
    **Ready to unlock growth through adoption?**
    
    1. **Schedule a Strategy Session** - Deep dive into your specific needs
    2. **Pilot Program** - Test with 3 universities in 30 days
    3. **Investment Discussion** - Explore partnership opportunities
    
    Contact: fernando@interviewquery.com | Schedule: calendly.com/iq-homeworks
    """)
    st.markdown('</div>', unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("*Interview Query Homeworks - Transforming B2U Success Through Adoption*")