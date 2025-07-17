import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import hashlib

# Page configuration
st.set_page_config(
    page_title="Satellite Imagery Challenge - Judging System",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Team data
TEAMS = [
    {"id": 1, "name": "MOD", "project": "Coherent Change Detection (CCD) & Displacement of Ballistic Missile Vehicles", "domain": "Defense", "data": "SAR, EO", "members": "Mohammed Albreiki, Suood Almazrouei"},
    {"id": 2, "name": "Aerial AI", "project": "Satellite-Based AI System for Urban Traffic Congestion Detection and Prediction in Abu Dhabi", "domain": "Urban Planning", "data": "EO", "members": "Mohammed Alameri, Ali Al Hashmi"},
    {"id": 3, "name": "Sard", "project": "Remote Desert Track Detection", "domain": "Border Security", "data": "SAR", "members": "Sara Alzaabi, Shahla Almazrouei"},
    {"id": 4, "name": "Land safer", "project": "Aircraft Fog Landing Index (FLI) for Abu Dhabi Airport", "domain": "Climate Monitoring", "data": "SAR", "members": "Rashed Alblooshi"},
    {"id": 5, "name": "MarEye", "project": "Intelligent Ship Detection for Enhanced Maritime Monitoring", "domain": "Maritime Monitoring", "data": "SAR", "members": "Ayesha Al Derei, Wazira Bawazeer"},
    {"id": 6, "name": "Rashed's team", "project": "UrbanTrack", "domain": "Urban Mobility", "data": "SAR, EO", "members": "Rashed Alaleeli, Kanaan Alwathaifi, Hassan Almazroui"},
    {"id": 7, "name": "mahra aldhaheri", "project": "Weather Pattern Identification and/or Early Warning Detection (with Alert)", "domain": "Climate Monitoring", "data": "EO", "members": "mahra aldhaheri"},
    {"id": 8, "name": "Pave Patrol", "project": "Road Cracks Detection", "domain": "Urban Planning", "data": "EO", "members": "Aysha Alhajeri, Hassan Alali"},
    {"id": 9, "name": "GeoPV", "project": "Detection and Classification of PV Panels Using Satellite Imagery and Geospatial Intelligence", "domain": "Environmental Monitoring", "data": "EO", "members": "Latifa Ali, Mariam Alnaqb"},
    {"id": 10, "name": "Asmaa team", "project": "Monitoring Oil Spill", "domain": "Environment Monitoring", "data": "EO, SAR", "members": "Asmaa Alhammadi, Asma Al Ali"},
    {"id": 11, "name": "Ghaf Root", "project": "The UAE National Tree Detection Through the Eyes of Satellites", "domain": "Urban Planning", "data": "EO", "members": "Bushra Alzadjali"},
    {"id": 12, "name": "GeoResQ", "project": "GeoResQ: Smart Earth Observation for Rescue", "domain": "Rescue", "data": "SAR, EO", "members": "Rawdha Majid Al Bedwawi, Nusaibah"},
    {"id": 13, "name": "Flood Sentinels", "project": "Detecting Flooded Urban Infrastructure SAR Satellite Imagery", "domain": "Disaster Management", "data": "SAR", "members": "Alyaa Almemari, Nouf Alhmoudi"},
    {"id": 14, "name": "DoubleA", "project": "Aircraft Detection & Classification", "domain": "Defense", "data": "EO", "members": "Abdulla Fadhel, Abdulla Aldhaen"},
    {"id": 15, "name": "TBD", "project": "ShamsEye: AI-Powered Satellite-Based Detection and Monitoring of Solar Panel Installations Using SAR and Optical Imagery", "domain": "Environment Monitoring", "data": "EO, SAR", "members": "Maryam Alshehhi, Bashayer Alsalami"}
]

# Evaluation criteria
CRITERIA = [
    {"id": "problem_definition", "name": "Problem Definition – significance & relevance", "weight": 15, "description": "Clarity and relevance of the problem being addressed"},
    {"id": "technical_execution", "name": "Technical Execution & method", "weight": 20, "description": "Quality of model development, data handling, and experimentation"},
    {"id": "results_interpretation", "name": "Results & Interpretation", "weight": 20, "description": "Quality and clarity of results, including metrics and visualizations"},
    {"id": "learning_reflection", "name": "Learning & Reflection", "weight": 10, "description": "Depth of understanding and reflection on challenges and lessons learned"},
    {"id": "presentation_quality", "name": "Presentation Quality (gIQ story)", "weight": 15, "description": "Clarity, structure, and professionalism of the presentation"},
    {"id": "long_term_vision", "name": "Long-Term Vision", "weight": 15, "description": "Connection between short-term work and future goals"},
    {"id": "scientific_evaluation", "name": "Scientific evaluation", "weight": 10, "description": "Originality and innovation of the proposal in relation to the subject matter of the challenge"},
    {"id": "team_expertise", "name": "Team relevant expertise", "weight": 10, "description": "Assesses the team's current and planned expertise related to the topic and application development, including strategies to acquire or supplement needed knowledge."}
]

# Score labels
SCORE_LABELS = {
    1: "Poor",
    2: "Fair", 
    3: "Satisfactory",
    4: "Good",
    5: "Excellent"
}

# Detailed score descriptions for each criterion
SCORE_DESCRIPTIONS = {
    "problem_definition": {
        1: "Vague or unclear",
        2: "Some relevance, lacks clarity",
        3: "Clear but generic",
        4: "Clear and relevant",
        5: "Clear, specific, and impactful"
    },
    "technical_execution": {
        1: "Minimal effort or errors",
        2: "Basic implementation",
        3: "Functional with some issues",
        4: "Well-executed and thoughtful",
        5: "Robust, innovative, and well-documented"
    },
    "results_interpretation": {
        1: "No results or unclear",
        2: "Basic results, limited insight",
        3: "Clear results, some interpretation",
        4: "Good results with meaningful insights",
        5: "Excellent results with deep analysis"
    },
    "learning_reflection": {
        1: "No reflection",
        2: "Minimal reflection",
        3: "Some learning evident",
        4: "Good insights and learning",
        5: "Strong reflection and growth demonstrated"
    },
    "presentation_quality": {
        1: "Disorganized or hard to follow",
        2: "Basic structure, lacks polish",
        3: "Clear and understandable",
        4: "Well-structured and engaging",
        5: "Highly professional and compelling"
    },
    "long_term_vision": {
        1: "No clear vision",
        2: "Vague or disconnected",
        3: "Some connection",
        4: "Clear and relevant extension",
        5: "Strong, innovative, and well-aligned vision"
    },
    "scientific_evaluation": {
        1: "Already in use, will not result in anything new",
        2: "Already in use, but gets better results with better features",
        3: "Common idea that may be used in a different way",
        4: "Common idea with new component/aspect of science",
        5: "Breakthrough science; new idea not done before"
    },
    "team_expertise": {
        1: "Team lacks relevant expertise and has no clear plan to acquire it.",
        2: "Team has limited expertise and vague plans to improve or supplement it.",
        3: "Team has some relevant expertise and basic plans to build or acquire more.",
        4: "Team has solid expertise and clear plans to fill any gaps.",
        5: "Team demonstrates strong expertise and proactive, well-defined strategies to ensure full capability."
    }
}

def get_session_file(judge_name):
    """Generate a unique session file name for each judge"""
    safe_name = "".join(c for c in judge_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    return f"session_{safe_name.replace(' ', '_')}.json"

def save_session(judge_name, data):
    """Save session data to file"""
    session_file = get_session_file(judge_name)
    try:
        with open(session_file, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving session: {e}")
        return False

def load_session(judge_name):
    """Load session data from file"""
    session_file = get_session_file(judge_name)
    try:
        if os.path.exists(session_file):
            with open(session_file, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Error loading session: {e}")
    return {}

def calculate_weighted_score(scores):
    """Calculate weighted score for a team"""
    total_score = 0
    for criterion in CRITERIA:
        if criterion['id'] in scores:
            total_score += scores[criterion['id']] * criterion['weight'] / 100
    return total_score

def export_results():
    """Export all results to CSV"""
    all_results = []
    
    # Get all session files
    session_files = [f for f in os.listdir('.') if f.startswith('session_') and f.endswith('.json')]
    
    for session_file in session_files:
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            judge_name = session_data.get('judge_name', 'Unknown')
            judge_email = session_data.get('judge_email', 'Unknown')
            
            for team in TEAMS:
                team_key = f"team_{team['id']}"
                if team_key in session_data:
                    team_data = session_data[team_key]
                    
                    result = {
                        'judge_name': judge_name,
                        'judge_email': judge_email,
                        'team_id': team['id'],
                        'team_name': team['name'],
                        'team_project': team['project'],
                        'submission_time': session_data.get('last_updated', 'Unknown')
                    }
                    
                    # Add scores
                    for criterion in CRITERIA:
                        result[f"{criterion['name']} ({criterion['weight']}%)"] = team_data.get(criterion['id'], 0)
                    
                    # Add weighted score
                    result['weighted_score'] = calculate_weighted_score(team_data)
                    
                    # Add comment
                    result['comment'] = team_data.get('comment', '')
                    
                    all_results.append(result)
        
        except Exception as e:
            st.error(f"Error processing {session_file}: {e}")
    
    if all_results:
        df = pd.DataFrame(all_results)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"judging_results_{timestamp}.csv"
        df.to_csv(filename, index=False)
        return filename, df
    
    return None, None

def main():
    st.title("🛰️ Satellite Imagery Challenge - Judging System")
    st.markdown("---")
    
    # Sidebar for judge information and navigation
    with st.sidebar:
        st.header("👨‍⚖️ Judge Information")
        
        # Judge details - Optional now
        judge_name = st.text_input("Judge Name (Optional)", key="judge_name", placeholder="Enter your name for saving progress")
        judge_email = st.text_input("Judge Email (Optional)", key="judge_email", placeholder="Enter your email")
        
        # If no name provided, create a temporary session
        if not judge_name:
            judge_name = f"Judge_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            st.info("💡 Enter your name above to save progress between sessions")
        
        # Load existing session
        session_data = load_session(judge_name)
        
        # Initialize session data if not exists
        if not session_data:
            session_data = {
                'judge_name': judge_name,
                'judge_email': judge_email or 'anonymous',
                'last_updated': datetime.now().isoformat()
            }
        
        if judge_name.startswith("Judge_"):
            st.warning("⚠️ Using temporary session - progress will be lost when you close the browser")
        else:
            st.success(f"Welcome, {judge_name}!")
        
        # Progress tracking
        st.header("📊 Progress")
        completed_teams = 0
        for team in TEAMS:
            team_key = f"team_{team['id']}"
            if team_key in session_data:
                team_data = session_data[team_key]
                if all(criterion['id'] in team_data for criterion in CRITERIA):
                    completed_teams += 1
        
        progress = completed_teams / len(TEAMS)
        st.progress(progress)
        st.write(f"Completed: {completed_teams}/{len(TEAMS)} teams")
        
        # Team navigation
        st.header("🎯 Team Navigation")
        
        # Get team ID from query params or default to 1
        default_team_id = int(st.query_params.get("team", 1))
        
        selected_team_id = st.selectbox(
            "Jump to team:",
            options=[team['id'] for team in TEAMS],
            format_func=lambda x: f"Team {x}: {next(t['name'] for t in TEAMS if t['id'] == x)}",
            index=default_team_id - 1,
            key="team_selector"
        )
        
        # Update query params when selection changes
        if selected_team_id != default_team_id:
            st.query_params["team"] = str(selected_team_id)
            st.rerun()
        
        # Auto-save toggle
        auto_save = st.checkbox("Auto-save progress", value=True)
        
        # Manual save button
        if st.button("💾 Save Progress"):
            if save_session(judge_name, session_data):
                st.success("Progress saved!")
            else:
                st.error("Failed to save progress")
        
        # Export results (admin only)
        st.header("📤 Export Results")
        if st.button("Export All Results"):
            filename, df = export_results()
            if filename:
                st.success(f"Results exported to {filename}")
                st.download_button(
                    label="Download Results",
                    data=df.to_csv(index=False),
                    file_name=filename,
                    mime="text/csv"
                )
            else:
                st.warning("No results to export")
    
    # Main content area
    selected_team = next(team for team in TEAMS if team['id'] == selected_team_id)
    team_key = f"team_{selected_team['id']}"
    
    # Initialize team data if not exists
    if team_key not in session_data:
        session_data[team_key] = {}
    
    # Display team information
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header(f"Team {selected_team['id']}: {selected_team['name']}")
        st.subheader(f"📋 {selected_team['project']}")
    
    with col2:
        # Team completion status
        team_scores = session_data[team_key]
        team_complete = all(criterion['id'] in team_scores for criterion in CRITERIA)
        if team_complete:
            st.success("✅ Complete")
            weighted_score = calculate_weighted_score(team_scores)
            st.metric("Weighted Score", f"{weighted_score:.2f}/5.0")
        else:
            st.warning("⏳ In Progress")
    
    # Team details
    st.info(f"**Domain:** {selected_team['domain']} | **Data:** {selected_team['data']} | **Members:** {selected_team['members']}")
    
    st.markdown("---")
    
    # Evaluation criteria
    st.header("📝 Evaluation Criteria")
    
    # Create tabs for better organization
    tab1, tab2 = st.tabs(["Evaluation", "Summary"])
    
    with tab1:
        for i, criterion in enumerate(CRITERIA):
            with st.expander(f"{criterion['name']} ({criterion['weight']}%)", expanded=True):
                st.write(f"**Description:** {criterion['description']}")
                
                # Score selection
                current_score = team_scores.get(criterion['id'], 1)
                
                col1, col2 = st.columns([2, 3])
                
                with col1:
                    score = st.radio(
                        f"Score:",
                        options=[1, 2, 3, 4, 5],
                        index=current_score - 1,
                        key=f"{team_key}_{criterion['id']}",
                        horizontal=True
                    )
                
                with col2:
                    # Show detailed descriptions
                    for score_val in [1, 2, 3, 4, 5]:
                        if score_val == score:
                            st.success(f"**{score_val} - {SCORE_LABELS[score_val]}:** {SCORE_DESCRIPTIONS[criterion['id']][score_val]}")
                        else:
                            st.write(f"**{score_val} - {SCORE_LABELS[score_val]}:** {SCORE_DESCRIPTIONS[criterion['id']][score_val]}")
                
                # Update session data
                team_scores[criterion['id']] = score
                
                # Auto-save
                if auto_save:
                    session_data['last_updated'] = datetime.now().isoformat()
                    save_session(judge_name, session_data)
        
        # Comments section
        st.subheader("💬 Comments")
        comment = st.text_area(
            f"Additional comments for {selected_team['name']}:",
            value=team_scores.get('comment', ''),
            height=100,
            key=f"{team_key}_comment"
        )
        
        team_scores['comment'] = comment
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if selected_team['id'] > 1:
                if st.button("⬅️ Previous Team", key="prev_team"):
                    # Save current progress before navigating
                    session_data['last_updated'] = datetime.now().isoformat()
                    save_session(judge_name, session_data)
                    st.query_params["team"] = str(selected_team['id'] - 1)
                    st.rerun()
        
        with col2:
            if st.button("💾 Save Team", key="save_team"):
                session_data['last_updated'] = datetime.now().isoformat()
                if save_session(judge_name, session_data):
                    st.success("Team evaluation saved!")
                else:
                    st.error("Failed to save team evaluation")
        
        with col3:
            if selected_team['id'] < len(TEAMS):
                if st.button("Next Team ➡️", key="next_team"):
                    # Save current progress before navigating
                    session_data['last_updated'] = datetime.now().isoformat()
                    save_session(judge_name, session_data)
                    st.query_params["team"] = str(selected_team['id'] + 1)
                    st.rerun()
    
    with tab2:
        st.subheader("📊 Team Summary")
        
        if team_complete:
            # Score breakdown
            st.write("**Score Breakdown:**")
            for criterion in CRITERIA:
                score = team_scores[criterion['id']]
                weighted_contribution = score * criterion['weight'] / 100
                st.write(f"- {criterion['name']}: {score}/5 ({SCORE_LABELS[score]}) → {weighted_contribution:.2f} points")
            
            # Total score
            total_weighted = calculate_weighted_score(team_scores)
            st.metric("**Total Weighted Score**", f"{total_weighted:.2f}/5.0")
            
            # Comment
            if team_scores.get('comment'):
                st.write(f"**Comment:** {team_scores['comment']}")
        else:
            st.warning("Complete all criteria to see the summary.")
    
    # Final submission
    if completed_teams == len(TEAMS):
        st.markdown("---")
        st.header("🎉 Evaluation Complete!")
        st.success(f"You have completed evaluating all {len(TEAMS)} teams!")
        
        if st.button("📤 Submit Final Evaluation", type="primary"):
            session_data['final_submission'] = datetime.now().isoformat()
            if save_session(judge_name, session_data):
                st.balloons()
                st.success("Final evaluation submitted successfully!")
            else:
                st.error("Failed to submit final evaluation")

if __name__ == "__main__":
    main()
