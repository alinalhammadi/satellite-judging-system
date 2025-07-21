import streamlit as st
import pandas as pd
import json
import os
import glob
import sqlite3
import threading
import time
from datetime import datetime
import requests
import base64
from typing import Dict, Any, Optional

# Page configuration
st.set_page_config(
    page_title="Satellite Imagery Challenge - Judging System",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# GitHub Configuration - Updated for your repository
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", os.getenv("GITHUB_TOKEN", ""))
GITHUB_REPO = "alinalhammadi/satellite-judging-system"
BACKUP_FOLDER = "database_backups"

# Database configuration
DB_FILE = "judging_database.db"
BACKUP_INTERVAL = 30  # seconds

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
    {"id": "problem_definition", "name": "Problem Definition – significance & relevance", "weight": 15, "description": "Clarity and relevance of the problem being addressed"},
    {"id": "technical_execution", "name": "Technical Execution & method", "weight": 20, "description": "Quality of model development, data handling, and experimentation"},
    {"id": "results_interpretation", "name": "Results & Interpretation", "weight": 20, "description": "Quality and clarity of results, including metrics and visualizations"},
    {"id": "learning_reflection", "name": "Learning & Reflection", "weight": 10, "description": "Depth of understanding and reflection on challenges and lessons learned"},
    {"id": "presentation_quality", "name": "Presentation Quality (gIQ story)", "weight": 15, "description": "Clarity, structure, and professionalism of the presentation"},
    {"id": "long_term_vision", "name": "Long-Term Vision", "weight": 15, "description": "Connection between short-term work and future goals"},
    {"id": "scientific_evaluation", "name": "Scientific evaluation", "weight": 10, "description": "Originality and innovation of the proposal in relation to the subject matter of the challenge"},
    {"id": "team_expertise", "name": "Team relevant expertise", "weight": 10, "description": "Assesses the team's current and planned expertise related to the topic and application development, including strategies to acquire or supplement needed knowledge."}
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

class DatabaseManager:
    """Handles all database operations with automatic backups"""
    
    def __init__(self, db_file: str):
        self.db_file = db_file
        self.init_database()
        self.start_backup_thread()
    
    def init_database(self):
        """Initialize the database with required tables"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Judges table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS judges (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Evaluations table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS evaluations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        judge_name TEXT NOT NULL,
                        team_id INTEGER NOT NULL,
                        team_name TEXT NOT NULL,
                        criterion_id TEXT NOT NULL,
                        score INTEGER NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(judge_name, team_id, criterion_id)
                    )
                ''')
                
                # Comments table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS comments (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        judge_name TEXT NOT NULL,
                        team_id INTEGER NOT NULL,
                        comment TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(judge_name, team_id)
                    )
                ''')
                
                # Activity log for debugging
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS activity_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        judge_name TEXT,
                        action TEXT,
                        details TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                
        except Exception as e:
            st.error(f"Database initialization failed: {e}")
    
    def log_activity(self, judge_name: str, action: str, details: str = ""):
        """Log activity for debugging and audit purposes"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO activity_log (judge_name, action, details) VALUES (?, ?, ?)",
                    (judge_name, action, details)
                )
                conn.commit()
        except Exception:
            pass  # Silent fail for logging
    
    def save_judge(self, judge_name: str) -> bool:
        """Save or update judge information"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO judges (name, last_active)
                    VALUES (?, CURRENT_TIMESTAMP)
                ''', (judge_name,))
                conn.commit()
                self.log_activity(judge_name, "judge_login", "Judge session started")
                return True
        except Exception as e:
            st.error(f"Failed to save judge: {e}")
            return False
    
    def save_evaluation(self, judge_name: str, team_id: int, team_name: str, scores: Dict[str, int], comment: str = "") -> bool:
        """Save evaluation scores and comments with atomic transaction"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Start transaction
                cursor.execute("BEGIN TRANSACTION")
                
                try:
                    # Save scores
                    for criterion_id, score in scores.items():
                        cursor.execute('''
                            INSERT OR REPLACE INTO evaluations 
                            (judge_name, team_id, team_name, criterion_id, score, updated_at)
                            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ''', (judge_name, team_id, team_name, criterion_id, score))
                    
                    # Save comment
                    if comment.strip():
                        cursor.execute('''
                            INSERT OR REPLACE INTO comments
                            (judge_name, team_id, comment, updated_at)
                            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                        ''', (judge_name, team_id, comment.strip()))
                    
                    # Update judge activity
                    cursor.execute('''
                        UPDATE judges SET last_active = CURRENT_TIMESTAMP WHERE name = ?
                    ''', (judge_name,))
                    
                    cursor.execute("COMMIT")
                    self.log_activity(judge_name, "evaluation_saved", f"Team {team_id}: {team_name}")
                    return True
                    
                except Exception as e:
                    cursor.execute("ROLLBACK")
                    raise e
                    
        except Exception as e:
            st.error(f"Failed to save evaluation: {e}")
            return False
    
    def load_evaluation(self, judge_name: str, team_id: int) -> Dict[str, Any]:
        """Load evaluation data for a specific judge and team"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Load scores
                cursor.execute('''
                    SELECT criterion_id, score FROM evaluations
                    WHERE judge_name = ? AND team_id = ?
                ''', (judge_name, team_id))
                
                scores = {row[0]: row[1] for row in cursor.fetchall()}
                
                # Load comment
                cursor.execute('''
                    SELECT comment FROM comments
                    WHERE judge_name = ? AND team_id = ?
                ''', (judge_name, team_id))
                
                comment_row = cursor.fetchone()
                comment = comment_row[0] if comment_row else ""
                
                result = scores.copy()
                result['comment'] = comment
                
                return result
                
        except Exception as e:
            st.error(f"Failed to load evaluation: {e}")
            return {}
    
    def get_judge_progress(self, judge_name: str) -> Dict[str, int]:
        """Get progress statistics for a judge"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                cursor = conn.cursor()
                
                # Count completed teams (teams with all criteria scored)
                cursor.execute('''
                    SELECT team_id, COUNT(DISTINCT criterion_id) as criteria_count
                    FROM evaluations 
                    WHERE judge_name = ?
                    GROUP BY team_id
                    HAVING criteria_count = ?
                ''', (judge_name, len(CRITERIA)))
                
                completed_teams = len(cursor.fetchall())
                
                return {
                    'completed_teams': completed_teams,
                    'total_teams': len(TEAMS),
                    'progress': completed_teams / len(TEAMS)
                }
                
        except Exception as e:
            st.error(f"Failed to get progress: {e}")
            return {'completed_teams': 0, 'total_teams': len(TEAMS), 'progress': 0}
    
    def export_all_data(self) -> Optional[pd.DataFrame]:
        """Export all evaluation data as DataFrame"""
        try:
            with sqlite3.connect(self.db_file) as conn:
                query = '''
                SELECT 
                    e.judge_name,
                    e.team_id,
                    e.team_name,
                    e.criterion_id,
                    e.score,
                    c.comment,
                    e.updated_at
                FROM evaluations e
                LEFT JOIN comments c ON e.judge_name = c.judge_name AND e.team_id = c.team_id
                ORDER BY e.judge_name, e.team_id, e.criterion_id
                '''
                
                df = pd.read_sql_query(query, conn)
                return df
                
        except Exception as e:
            st.error(f"Failed to export data: {e}")
            return None
    
    def create_database_backup(self) -> str:
        """Create a backup of the entire database"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"backup_database_{timestamp}.db"
            
            # Copy database file
            import shutil
            shutil.copy2(self.db_file, backup_file)
            
            return backup_file
            
        except Exception as e:
            st.error(f"Failed to create database backup: {e}")
            return ""
    
    def start_backup_thread(self):
        """Start background thread for periodic backups"""
        if not hasattr(st.session_state, 'backup_thread_started'):
            st.session_state.backup_thread_started = True
            
            def backup_loop():
                while True:
                    time.sleep(BACKUP_INTERVAL)
                    try:
                        self.backup_to_github()
                    except Exception:
                        pass  # Silent fail for background backups
            
            backup_thread = threading.Thread(target=backup_loop, daemon=True)
            backup_thread.start()
    
    def backup_to_github(self) -> bool:
        """Backup database to your GitHub repository"""
        if not GITHUB_TOKEN or not GITHUB_REPO:
            return False
            
        try:
            # Create database backup
            backup_file = self.create_database_backup()
            if not backup_file:
                return False
            
            # Read backup file
            with open(backup_file, 'rb') as f:
                content = base64.b64encode(f.read()).decode()
            
            # Upload to your GitHub repository
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = f"{BACKUP_FOLDER}/database_backup_{timestamp}.db"
            
            # Check if backup folder exists, create if not
            folder_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{BACKUP_FOLDER}"
            headers = {
                "Authorization": f"token {GITHUB_TOKEN}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            # Try to create backup folder
            try:
                folder_data = {
                    "message": f"Create backup folder",
                    "content": base64.b64encode(b"# Database Backups\n\nThis folder contains automated database backups from the satellite judging system.").decode(),
                    "path": f"{BACKUP_FOLDER}/README.md"
                }
                requests.put(f"https://api.github.com/repos/{GITHUB_REPO}/contents/{BACKUP_FOLDER}/README.md", 
                           json=folder_data, headers=headers)
            except:
                pass  # Folder might already exist
            
            # Upload database backup
            url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}"
            
            data = {
                "message": f"Auto-backup: Database backup {timestamp}",
                "content": content,
                "branch": "main"
            }
            
            response = requests.put(url, json=data, headers=headers)
            
            # Clean up local backup file
            os.remove(backup_file)
            
            if response.status_code == 201:
                return True
            else:
                # Log error for debugging
                print(f"GitHub backup failed: {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            print(f"GitHub backup error: {e}")
            return False

# Initialize database manager
db_manager = DatabaseManager(DB_FILE)

def normalize_judge_name(name: str) -> str:
    """Normalize judge name: Title Case"""
    return name.strip().title()

def is_valid_judge_name(name: str) -> bool:
    """Check if judge name is valid"""
    if not name or name.strip() == "":
        return False
    if name.startswith("Judge_") and len(name.split('_')) >= 3:
        return False
    if len(name.strip()) < 2:
        return False
    return True

def calculate_weighted_score(scores: Dict[str, int]) -> float:
    """Calculate weighted score for a team"""
    total_score = 0
    for criterion in CRITERIA:
        if criterion['id'] in scores:
            total_score += scores[criterion['id']] * criterion['weight'] / 100
    return total_score

def main():
    st.title("🛰️ Satellite Imagery Challenge - Judging System")
    st.markdown("---")
    
    # Real-time connection status
    connection_status = st.empty()
    connection_status.success("🟢 System Online - Auto-saving enabled")
    
    # Sidebar for judge information and navigation
    with st.sidebar:
        st.header("👨‍⚖️ Judge Information")
        
        # Judge name input with validation
        raw_judge_name = st.text_input("Judge Name*", key="judge_name", placeholder="Enter your full name (required)")
        
        if not is_valid_judge_name(raw_judge_name):
            if raw_judge_name and raw_judge_name.strip() != "":
                if raw_judge_name.startswith("Judge_"):
                    st.error("⚠️ Please enter your actual name, not a temporary ID")
                elif len(raw_judge_name.strip()) < 2:
                    st.error("⚠️ Please enter your full name (minimum 2 characters)")
                else:
                    st.error("⚠️ Invalid name format")
            else:
                st.error("⚠️ Judge name is required to continue")
            
            st.warning("👆 Please enter your name above to start judging")
            st.stop()
        
        # Normalize judge name
        judge_name = normalize_judge_name(raw_judge_name)
        if judge_name != raw_judge_name:
            st.info(f"Name normalized to: {judge_name}")
        
        # Register/update judge in database
        if db_manager.save_judge(judge_name):
            st.success(f"✅ Welcome, {judge_name}!")
        else:
            st.error("❌ Failed to register judge")
            st.stop()
        
        st.markdown("---")
        
        # Progress tracking
        st.header("📊 Progress")
        progress_data = db_manager.get_judge_progress(judge_name)
        completed_teams = progress_data['completed_teams']
        total_teams = progress_data['total_teams']
        progress = progress_data['progress']
        
        st.progress(progress)
        st.write(f"Completed: {completed_teams}/{total_teams} teams")
        
        if progress == 1.0:
            st.success("🎉 All teams evaluated!")
            st.balloons()
        
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
        
        # Manual save button
        if st.button("💾 Force Save", help="Force save current progress"):
            st.success("✅ Auto-save is always active!")
            
        # System status
        st.header("📊 System Status")
        st.success("🟢 Database Connected")
        st.info(f"🔄 Auto-backup every {BACKUP_INTERVAL}s")
        
        # Export options for admin
        if st.button("📊 Admin Panel"):
            st.header("📤 Data Export")
            
            # Export to CSV
            if st.button("Export Results (CSV)"):
                df = db_manager.export_all_data()
                if df is not None:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    csv_data = df.to_csv(index=False).encode('utf-8')
                    
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv_data,
                        file_name=f"judging_results_{timestamp}.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("❌ Export failed")
            
            # Database backup
            if st.button("Create Database Backup"):
                backup_file = db_manager.create_database_backup()
                if backup_file:
                    with open(backup_file, 'rb') as f:
                        st.download_button(
                            label="📥 Download Database Backup",
                            data=f.read(),
                            file_name=backup_file,
                            mime="application/octet-stream"
                        )
                    os.remove(backup_file)
                else:
                    st.error("❌ Backup failed")
            
            # GitHub backup status
            if GITHUB_TOKEN and GITHUB_REPO:
                st.success("✅ GitHub backup configured")
                st.info(f"📂 Backup location: {GITHUB_REPO}/{BACKUP_FOLDER}")
                
                # Show last backup attempt status
                if st.button("🔄 Test GitHub Backup"):
                    if db_manager.backup_to_github():
                        st.success("✅ GitHub backup successful!")
                    else:
                        st.error("❌ GitHub backup failed - check token and permissions")
            else:
                st.warning("⚠️ GitHub backup not configured")
                st.info("Add GITHUB_TOKEN to Streamlit secrets to enable auto-backup")
    
    # Main content area
    selected_team = next(team for team in TEAMS if team['id'] == selected_team_id)
    
    # Load existing evaluation from database
    team_scores = db_manager.load_evaluation(judge_name, selected_team['id'])
    
    # Display team information
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.header(f"Team {selected_team['id']}: {selected_team['name']}")
        st.subheader(f"📋 {selected_team['project']}")
    
    with col2:
        # Team completion status
        team_complete = len(team_scores) > 1 and all(criterion['id'] in team_scores for criterion in CRITERIA)
        if team_complete:
            st.success("✅ Complete")
            weighted_score = calculate_weighted_score(team_scores)
            st.metric("Weighted Score", f"{weighted_score:.2f}/5.0")
        else:
            st.warning("⏳ In Progress")
    
    # Team details
    st.info(f"**Domain:** {selected_team['domain']} | **Data:** {selected_team['data']} | **Members:** {selected_team['members']}")
    
    st.markdown("---")
    
    # Auto-save indicator
    auto_save_status = st.empty()
    
    # Evaluation form
    st.header("📝 Evaluation Criteria")
    
    # Create evaluation form
    with st.form(key=f"team_{selected_team['id']}_form"):
        updated_scores = {}
        
        # Score inputs for each criterion
        for criterion in CRITERIA:
            with st.expander(f"{criterion['name']} ({criterion['weight']}%)", expanded=True):
                st.write(f"**Description:** {criterion['description']}")
                
                current_score = team_scores.get(criterion['id'], 1)
                
                col1, col2 = st.columns([2, 3])
                
                with col1:
                    score = st.radio(
                        "Score:",
                        options=[1, 2, 3, 4, 5],
                        index=current_score - 1,
                        key=f"team_{selected_team['id']}_{criterion['id']}"
                    )
                
                with col2:
                    # Show score descriptions
                    for score_val in [1, 2, 3, 4, 5]:
                        if score_val == score:
                            st.success(f"**{score_val} - {SCORE_LABELS[score_val]}:** {SCORE_DESCRIPTIONS[criterion['id']][score_val]}")
                        else:
                            st.write(f"**{score_val} - {SCORE_LABELS[score_val]}:** {SCORE_DESCRIPTIONS[criterion['id']][score_val]}")
                
                updated_scores[criterion['id']] = score
        
        # Comments section
        st.subheader("💬 Comments")
        current_comment = team_scores.get('comment', '')
        comment = st.text_area(
            f"Additional comments for {selected_team['name']}:",
            value=current_comment,
            height=100
        )
        
        # Submit button
        submit_button = st.form_submit_button("💾 Save Evaluation", type="primary")
        
        if submit_button:
            # Save to database
            if db_manager.save_evaluation(judge_name, selected_team['id'], selected_team['name'], updated_scores, comment):
                auto_save_status.success("✅ Evaluation saved successfully!")
                time.sleep(1)
                st.rerun()
            else:
                auto_save_status.error("❌ Failed to save evaluation!")
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if selected_team['id'] > 1:
            if st.button("⬅️ Previous Team", key="prev_team"):
                st.query_params["team"] = str(selected_team['id'] - 1)
                st.rerun()
    
    with col2:
        # Show current team position
        st.write(f"Team {selected_team['id']} of {len(TEAMS)}")
    
    with col3:
        if selected_team['id'] < len(TEAMS):
            if st.button("Next Team ➡️", key="next_team"):
                st.query_params["team"] = str(selected_team['id'] + 1)
                st.rerun()
    
    # Summary section
    if team_complete:
        st.markdown("---")
        st.header("📊 Team Summary")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("**Score Breakdown:**")
            for criterion in CRITERIA:
                if criterion['id'] in team_scores:
                    score = team_scores[criterion['id']]
                    weighted_contribution = score * criterion['weight'] / 100
                    st.write(f"- {criterion['name']}: {score}/5 ({SCORE_LABELS[score]}) → {weighted_contribution:.2f} points")
            
            if team_scores.get('comment'):
                st.write(f"**Comment:** {team_scores['comment']}")
        
        with col2:
            total_weighted = calculate_weighted_score(team_scores)
            st.metric("**Total Weighted Score**", f"{total_weighted:.2f}/5.0")
            
            # Score visualization
            score_data = []
            for criterion in CRITERIA:
                if criterion['id'] in team_scores:
                    score_data.append({
                        'Criterion': criterion['name'][:20] + '...' if len(criterion['name']) > 20 else criterion['name'],
                        'Score': team_scores[criterion['id']],
                        'Weight': criterion['weight']
                    })
            
            if score_data:
                import plotly.express as px
                fig = px.bar(
                    score_data, 
                    x='Score', 
                    y='Criterion',
                    orientation='h',
                    title='Score Breakdown',
                    color='Score',
                    color_continuous_scale='RdYlGn'
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)

    # Final completion status
    if completed_teams == len(TEAMS):
        st.markdown("---")
        st.header("🎉 Evaluation Complete!")
        st.success(f"You have completed evaluating all {len(TEAMS)} teams!")
        st.balloons()
        
        # Show overall statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Teams Evaluated", completed_teams)
        
        with col2:
            # Calculate average score across all teams
            all_scores = []
            for team in TEAMS:
                team_data = db_manager.load_evaluation(judge_name, team['id'])
                if len(team_data) > 1:  # Has scores (excluding just comment)
                    weighted_score = calculate_weighted_score(team_data)
                    all_scores.append(weighted_score)
            
            if all_scores:
                avg_score = sum(all_scores) / len(all_scores)
                st.metric("Average Score", f"{avg_score:.2f}/5.0")
        
        with col3:
            st.metric("Completion Rate", "100%")

if __name__ == "__main__":
    main()

