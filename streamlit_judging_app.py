import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import json
import time

# Page configuration
st.set_page_config(
    page_title="Satellite Imagery Challenge - Judging System",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Team data (final order and names)
TEAMS = [
    {"id": 1, "name": "MOD", "project": "Coherent Change Detection (CCD) & Displacement of Ballistic Missile Vehicles", "domain": "Defense", "data": "SAR, EO", "members": "Mohamed Albreiki, Suood Almazrouei"},
    {"id": 2, "name": "Ghaf Root", "project": "The UAE National Tree Detection Through the Eyes of Satellites", "domain": "Urban Planning", "data": "EO", "members": "Bushra Alzadjali"},
    {"id": 3, "name": "DoubleA", "project": "Aircraft Detection & Classification", "domain": "Defense", "data": "EO", "members": "Abdulla Fadhel, Abdulla Aldhaen"},
    {"id": 4, "name": "GeoResQ", "project": "GeoResQ: Smart Earth Observation for Rescue", "domain": "Rescue", "data": "SAR, EO", "members": "Rawdha Al Bedwawi, Nusaibah Alhemeiri"},
    {"id": 5, "name": "FalconRadar", "project": "Aircraft Fog Landing Index (FLI) for Abu Dhabi Airport", "domain": "Climate Monitoring", "data": "SAR", "members": "Rashed Alblooshi"},
    {"id": 6, "name": "Pave Patrol", "project": "Road Cracks Detection", "domain": "Urban Planning", "data": "EO", "members": "Aysha Alhajeri, Hassan Al Ali"},
    {"id": 7, "name": "TBD", "project": "ShamsEye: AI-Powered Satellite-Based Detection and Monitoring of Solar Panel Installations Using SAR and Optical Imagery", "domain": "Environment Monitoring", "data": "EO, SAR", "members": "Maryam Alshehhi, Bashayer Alsalami"},
    {"id": 8, "name": "Mahra Al Dhaheri", "project": "Weather Pattern Identification and/or Early Warning Detection (with Alert)", "domain": "Climate Monitoring", "data": "EO", "members": "Mahra Al Dhaheri"},
    {"id": 9, "name": "MarEye", "project": "Intelligent Ship Detection for Enhanced Maritime Monitoring", "domain": "Maritime Monitoring", "data": "SAR", "members": "Ayesha Alderei, Wazira Bawazeer"},
    {"id": 10, "name": "UrbanTrack", "project": "UrbanTrack", "domain": "Urban Mobility", "data": "SAR, EO", "members": "Rashed Alaleeli, Kanaan Alwathaifi, Hassan Almazroueoi"},
    {"id": 11, "name": "Asmaa team", "project": "Monitoring Oil Spill", "domain": "Environment Monitoring", "data": "EO, SAR", "members": "Asmaa Alhammadi, Asma Al Ali"},
    {"id": 12, "name": "Flood Sentinels", "project": "Detecting Flooded Urban Infrastructure SAR Satellite Imagery", "domain": "Disaster Management", "data": "SAR", "members": "Nouf Alhmoudi, Alyaa Almemari"},
    {"id": 13, "name": "Sard", "project": "Remote Desert Track Detection", "domain": "Border Security", "data": "SAR", "members": "Sara Alzaabi, Shahla Almazrouei"},
    {"id": 14, "name": "Aerial AI", "project": "Satellite-Based AI System for Urban Traffic Congestion Detection and Prediction in Abu Dhabi", "domain": "Urban Planning", "data": "EO", "members": "Mohammed Alameri, Ali Alhashmi"},
    {"id": 15, "name": "GeoPV", "project": "Detection and Classification of PV Panels Using Satellite Imagery and Geospatial Intelligence", "domain": "Environmental Monitoring", "data": "EO", "members": "Latifa Albaeek, Mariam Alnaqbi"}
]

# Evaluation criteria
CRITERIA = [
    {"id": "problem_definition", "name": "Problem Definition – significance & relevance", "weight": 15},
    {"id": "technical_execution", "name": "Technical Execution & method", "weight": 20},
    {"id": "results_interpretation", "name": "Results & Interpretation", "weight": 20},
    {"id": "learning_reflection", "name": "Learning & Reflection", "weight": 10},
    {"id": "presentation_quality", "name": "Presentation Quality (gIQ story)", "weight": 15},
    {"id": "long_term_vision", "name": "Long-Term Vision", "weight": 15},
    {"id": "scientific_evaluation", "name": "Scientific evaluation", "weight": 10},
    {"id": "team_expertise", "name": "Team relevant expertise", "weight": 10}
]

# Score labels and descriptions
SCORE_LABELS = {1: "Poor", 2: "Fair", 3: "Satisfactory", 4: "Good", 5: "Excellent"}

SCORE_DESCRIPTIONS = {
    "problem_definition": {
        1: "Vague or unclear", 2: "Some relevance, lacks clarity", 3: "Clear but generic", 
        4: "Clear and relevant", 5: "Clear, specific, and impactful"
    },
    "technical_execution": {
        1: "Minimal effort or errors", 2: "Basic implementation", 3: "Functional with some issues", 
        4: "Well-executed and thoughtful", 5: "Robust, innovative, and well-documented"
    },
    "results_interpretation": {
        1: "No results or unclear", 2: "Basic results, limited insight", 3: "Clear results, some interpretation", 
        4: "Good results with meaningful insights", 5: "Excellent results with deep analysis"
    },
    "learning_reflection": {
        1: "No reflection", 2: "Minimal reflection", 3: "Some learning evident", 
        4: "Good insights and learning", 5: "Strong reflection and growth demonstrated"
    },
    "presentation_quality": {
        1: "Disorganized or hard to follow", 2: "Basic structure, lacks polish", 3: "Clear and understandable", 
        4: "Well-structured and engaging", 5: "Highly professional and compelling"
    },
    "long_term_vision": {
        1: "No clear vision", 2: "Vague or disconnected", 3: "Some connection", 
        4: "Clear and relevant extension", 5: "Strong, innovative, and well-aligned vision"
    },
    "scientific_evaluation": {
        1: "Already in use, will not result in anything new", 2: "Already in use, but gets better results with better features", 
        3: "Common idea that may be used in a different way", 4: "Common idea with new component/aspect of science", 
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

# Database functions
def init_database():
    """Initialize SQLite database with required tables"""
    try:
        conn = sqlite3.connect('judging.db')
        cursor = conn.cursor()
        
        # Create evaluations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                judge_name TEXT NOT NULL,
                team_id INTEGER NOT NULL,
                team_name TEXT NOT NULL,
                problem_definition INTEGER DEFAULT 1,
                technical_execution INTEGER DEFAULT 1,
                results_interpretation INTEGER DEFAULT 1,
                learning_reflection INTEGER DEFAULT 1,
                presentation_quality INTEGER DEFAULT 1,
                long_term_vision INTEGER DEFAULT 1,
                scientific_evaluation INTEGER DEFAULT 1,
                team_expertise INTEGER DEFAULT 1,
                comment TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(judge_name, team_id)
            )
        ''')
        
        # Create judges table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS judges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                judge_name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database initialization failed: {e}")
        return False

def normalize_judge_name(name):
    """Normalize judge name: Title Case"""
    return name.strip().title()

def save_judge(judge_name):
    """Save or update judge in database"""
    try:
        conn = sqlite3.connect('judging.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO judges (judge_name, last_active) 
            VALUES (?, ?)
        ''', (judge_name, datetime.now()))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Failed to save judge: {e}")
        return False

def save_evaluation(judge_name, team_id, team_name, scores, comment=""):
    """Save team evaluation to database"""
    try:
        conn = sqlite3.connect('judging.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO evaluations 
            (judge_name, team_id, team_name, problem_definition, technical_execution, 
             results_interpretation, learning_reflection, presentation_quality, 
             long_term_vision, scientific_evaluation, team_expertise, comment, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            judge_name, team_id, team_name,
            scores.get('problem_definition', 1),
            scores.get('technical_execution', 1), 
            scores.get('results_interpretation', 1),
            scores.get('learning_reflection', 1),
            scores.get('presentation_quality', 1),
            scores.get('long_term_vision', 1),
            scores.get('scientific_evaluation', 1),
            scores.get('team_expertise', 1),
            comment,
            datetime.now()
        ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Failed to save evaluation: {e}")
        return False

def load_evaluation(judge_name, team_id):
    """Load evaluation from database"""
    try:
        conn = sqlite3.connect('judging.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT problem_definition, technical_execution, results_interpretation,
                   learning_reflection, presentation_quality, long_term_vision,
                   scientific_evaluation, team_expertise, comment
            FROM evaluations 
            WHERE judge_name = ? AND team_id = ?
        ''', (judge_name, team_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'problem_definition': result[0],
                'technical_execution': result[1],
                'results_interpretation': result[2],
                'learning_reflection': result[3],
                'presentation_quality': result[4],
                'long_term_vision': result[5],
                'scientific_evaluation': result[6],
                'team_expertise': result[7],
                'comment': result[8] or ''
            }
        return {}
    except Exception as e:
        st.error(f"Failed to load evaluation: {e}")
        return {}

def get_judge_progress(judge_name):
    """Get judge's progress statistics"""
    try:
        conn = sqlite3.connect('judging.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM evaluations WHERE judge_name = ?
        ''', (judge_name,))
        
        completed = cursor.fetchone()[0]
        conn.close()
        return completed, len(TEAMS)
    except:
        return 0, len(TEAMS)

def export_all_results():
    """Export all results from database to DataFrame"""
    try:
        conn = sqlite3.connect('judging.db')
        
        query = '''
            SELECT 
                judge_name,
                team_id,
                team_name,
                problem_definition,
                technical_execution,
                results_interpretation,
                learning_reflection,
                presentation_quality,
                long_term_vision,
                scientific_evaluation,
                team_expertise,
                comment,
                updated_at as submission_time
            FROM evaluations 
            ORDER BY judge_name, team_id
        '''
        
        df = pd.read_sql_query(query, conn)
        
        if not df.empty:
            # Calculate weighted scores
            df['weighted_score'] = (
                df['problem_definition'] * 0.15 +
                df['technical_execution'] * 0.20 +
                df['results_interpretation'] * 0.20 +
                df['learning_reflection'] * 0.10 +
                df['presentation_quality'] * 0.15 +
                df['long_term_vision'] * 0.15 +
                df['scientific_evaluation'] * 0.10 +
                df['team_expertise'] * 0.10
            ).round(2)
            
            # Add team project info
            team_info = {team['id']: team['project'] for team in TEAMS}
            df['team_project'] = df['team_id'].map(team_info)
        
        conn.close()
        return df
        
    except Exception as e:
        st.error(f"Export failed: {e}")
        return pd.DataFrame()

def calculate_weighted_score(scores):
    """Calculate weighted score for a team"""
    total_score = 0
    for criterion in CRITERIA:
        if criterion['id'] in scores:
            total_score += scores[criterion['id']] * criterion['weight'] / 100
    return total_score

def main():
    st.title("🛰️ Satellite Imagery Challenge - Judging System")
    st.markdown("---")
    
    # Initialize database
    if not init_database():
        st.error("❌ Database initialization failed!")
        st.stop()
    
    # Sidebar for judge information and navigation
    with st.sidebar:
        st.header("👨‍⚖️ Judge Information")
        
        # Judge name - MANDATORY
        raw_judge_name = st.text_input("Judge Name*", key="judge_name", placeholder="Enter your full name (required)")
        
        if not raw_judge_name or raw_judge_name.strip() == "" or len(raw_judge_name.strip()) < 2:
            st.error("⚠️ Please enter your full name to continue")
            st.stop()
        
        # Normalize judge name
        judge_name = normalize_judge_name(raw_judge_name)
        if judge_name != raw_judge_name:
            st.info(f"Name normalized to: {judge_name}")
        
        # Save judge to database
        if save_judge(judge_name):
            st.success(f"✅ Welcome, {judge_name}!")
        else:
            st.error("❌ Failed to save judge info")
        
        st.markdown("---")
        
        # Progress tracking
        st.header("📊 Progress")
        completed_teams, total_teams = get_judge_progress(judge_name)
        progress = completed_teams / total_teams if total_teams > 0 else 0
        st.progress(progress)
        st.write(f"Completed: {completed_teams}/{total_teams} teams")
        
        # Team navigation
        st.header("🎯 Team Navigation")
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
        
        # Export section (admin)
        if st.button("🔧 Admin Panel", help="System admin access"):
            st.header("📤 Export Results")
            
            # Show stats
            try:
                conn = sqlite3.connect('judging.db')
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(DISTINCT judge_name) FROM evaluations")
                judge_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM evaluations")
                eval_count = cursor.fetchone()[0]
                
                conn.close()
                
                st.info(f"Database contains {judge_count} judges with {eval_count} evaluations")
                
                if st.button("📊 Export to CSV"):
                    df = export_all_results()
                    if not df.empty:
                        st.success(f"✅ Exported {len(df)} evaluations")
                        
                        # Show preview
                        st.dataframe(df.head(10))
                        
                        # Download button
                        csv_data = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Results CSV",
                            data=csv_data,
                            file_name=f"judging_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            type="primary"
                        )
                    else:
                        st.warning("No data to export")
                        
            except Exception as e:
                st.error(f"Database error: {e}")
    
    # Main content area
    selected_team = next(team for team in TEAMS if team['id'] == selected_team_id)
    
    # Load existing evaluation
    team_scores = load_evaluation(judge_name, selected_team['id'])
    
    # Display team information
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header(f"Team {selected_team['id']}: {selected_team['name']}")
        st.subheader(f"📋 {selected_team['project']}")
    
    with col2:
        # Team completion status
        team_complete = len(team_scores) > 0 and all(criterion['id'] in team_scores for criterion in CRITERIA)
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
        # Track if any changes were made
        changes_made = False
        updated_scores = {}
        
        for criterion in CRITERIA:
            with st.expander(f"{criterion['name']} ({criterion['weight']}%)", expanded=True):
                st.write(f"**Description:** Assesses {criterion['name'].lower()}")
                
                # Score selection
                current_score = team_scores.get(criterion['id'], 1)
                
                col1, col2 = st.columns([2, 3])
                
                with col1:
                    score = st.radio(
                        f"Score:",
                        options=[1, 2, 3, 4, 5],
                        index=current_score - 1,
                        key=f"team_{selected_team['id']}_{criterion['id']}",
                        horizontal=True
                    )
                
                with col2:
                    # Show detailed descriptions
                    for score_val in [1, 2, 3, 4, 5]:
                        if score_val == score:
                            st.success(f"**{score_val} - {SCORE_LABELS[score_val]}:** {SCORE_DESCRIPTIONS[criterion['id']][score_val]}")
                        else:
                            st.write(f"**{score_val} - {SCORE_LABELS[score_val]}:** {SCORE_DESCRIPTIONS[criterion['id']][score_val]}")
                
                updated_scores[criterion['id']] = score
                
                if score != current_score:
                    changes_made = True
        
        # Comments section
        st.subheader("💬 Comments")
        current_comment = team_scores.get('comment', '')
        comment = st.text_area(
            f"Additional comments for {selected_team['name']}:",
            value=current_comment,
            height=100,
            key=f"team_{selected_team['id']}_comment"
        )
        
        if comment != current_comment:
            changes_made = True
        
        # Auto-save when changes are made
        if changes_made:
            if save_evaluation(judge_name, selected_team['id'], selected_team['name'], updated_scores, comment):
                st.success("✅ Changes saved automatically!")
                # Brief pause then reload to reflect changes
                st.rerun()
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if selected_team['id'] > 1:
                if st.button("⬅️ Previous Team", key="prev_team"):
                    st.query_params["team"] = str(selected_team['id'] - 1)
                    st.rerun()
        
        with col2:
            if st.button("💾 Save Team", key="save_team"):
                if save_evaluation(judge_name, selected_team['id'], selected_team['name'], updated_scores, comment):
                    st.success("✅ Team saved!")
                else:
                    st.error("❌ Save failed")
        
        with col3:
            if selected_team['id'] < len(TEAMS):
                if st.button("Next Team ➡️", key="next_team"):
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
        st.balloons()

if __name__ == "__main__":
    main()
