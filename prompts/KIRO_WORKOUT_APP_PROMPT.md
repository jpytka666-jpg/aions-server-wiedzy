# KIRO TASK: Build AI Workout Tracker App

## OVERVIEW
Build a self-hosted AI workout tracking application with progressive overload automation. The app runs entirely on local machine with Phi-3 LLM for intelligent recommendations.

## LOCATION SETUP
1. Find Phi-3 model on D:\ drive (search for phi3 or phi-3 files, likely in Ollama folder or standalone .gguf)
2. Create project in location user specifies
3. All data stays local - no cloud dependencies

---

## PHASE 1: PROJECT STRUCTURE

Create this folder structure:
```
workout-tracker/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # PostgreSQL connection
│   │   ├── models.py            # SQLAlchemy models
│   │   ├── schemas.py           # Pydantic schemas
│   │   ├── routers/
│   │   │   ├── workouts.py      # Workout CRUD
│   │   │   ├── exercises.py     # Exercise library
│   │   │   ├── progress.py      # Progress tracking
│   │   │   └── ai.py            # AI recommendations
│   │   ├── services/
│   │   │   ├── progression.py   # Progressive overload logic
│   │   │   ├── ai_coach.py      # Phi-3 integration
│   │   │   └── memory.py        # ChromaDB context
│   │   └── utils/
│   │       └── calculations.py  # 1RM, volume calculations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   └── api/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## PHASE 2: BACKEND SETUP

### Step 2.1: requirements.txt
```
fastapi==0.109.0
uvicorn==0.27.0
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
pydantic==2.5.3
chromadb==0.4.22
ollama==0.1.6
python-dotenv==1.0.0
alembic==1.13.1
```

### Step 2.2: config.py
```python
from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://workout:workout123@localhost:5432/workout_db"
    CHROMADB_PATH: str = "./chromadb_data"
    OLLAMA_HOST: str = "http://localhost:11434"
    PHI3_MODEL: str = "phi3"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### Step 2.3: database.py
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Step 2.4: models.py
```python
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from .database import Base

class MuscleGroup(enum.Enum):
    CHEST = "chest"
    BACK = "back"
    SHOULDERS = "shoulders"
    LEGS = "legs"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    CORE = "core"
    FOREARMS = "forearms"
    GLUTES = "glutes"
    CALVES = "calves"

class ExerciseType(enum.Enum):
    COMPOUND = "compound"
    ISOLATION = "isolation"
    CARDIO = "cardio"

class Exercise(Base):
    __tablename__ = "exercises"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    muscle_group = Column(String(50))
    secondary_muscles = Column(String(200), nullable=True)
    exercise_type = Column(String(20))
    equipment = Column(String(100), nullable=True)
    instructions = Column(Text, nullable=True)
    video_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class WorkoutPlan(Base):
    __tablename__ = "workout_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    description = Column(Text, nullable=True)
    days_per_week = Column(Integer, default=4)
    plan_type = Column(String(50))  # FBW, PPL, Upper/Lower, etc.
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    days = relationship("WorkoutDay", back_populates="plan")

class WorkoutDay(Base):
    __tablename__ = "workout_days"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("workout_plans.id"))
    day_number = Column(Integer)  # 1, 2, 3, 4 for 4-day rotation
    name = Column(String(100))  # "Day A - Chest Priority"
    priority_muscle = Column(String(50))  # Main focus
    
    plan = relationship("WorkoutPlan", back_populates="days")
    planned_exercises = relationship("PlannedExercise", back_populates="day")

class PlannedExercise(Base):
    __tablename__ = "planned_exercises"
    
    id = Column(Integer, primary_key=True, index=True)
    day_id = Column(Integer, ForeignKey("workout_days.id"))
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    order = Column(Integer)
    target_sets = Column(Integer, default=4)
    target_reps_min = Column(Integer, default=6)
    target_reps_max = Column(Integer, default=8)
    is_priority = Column(Boolean, default=False)  # 50% priority, 50% supporting
    
    day = relationship("WorkoutDay", back_populates="planned_exercises")
    exercise = relationship("Exercise")

class WorkoutSession(Base):
    __tablename__ = "workout_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    plan_id = Column(Integer, ForeignKey("workout_plans.id"))
    day_id = Column(Integer, ForeignKey("workout_days.id"))
    date = Column(DateTime, default=datetime.utcnow)
    duration_minutes = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    fatigue_level = Column(Integer, nullable=True)  # 1-10
    completed = Column(Boolean, default=False)
    
    sets = relationship("ExerciseSet", back_populates="session")

class ExerciseSet(Base):
    __tablename__ = "exercise_sets"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("workout_sessions.id"))
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    set_number = Column(Integer)
    reps = Column(Integer)
    weight = Column(Float)
    rpe = Column(Float, nullable=True)  # Rate of Perceived Exertion 1-10
    rir = Column(Integer, nullable=True)  # Reps In Reserve
    is_warmup = Column(Boolean, default=False)
    notes = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("WorkoutSession", back_populates="sets")
    exercise = relationship("Exercise")

class PersonalRecord(Base):
    __tablename__ = "personal_records"
    
    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    date = Column(DateTime, default=datetime.utcnow)
    weight = Column(Float)
    reps = Column(Integer)
    estimated_1rm = Column(Float)
    
    exercise = relationship("Exercise")

class MuscleRecovery(Base):
    __tablename__ = "muscle_recovery"
    
    id = Column(Integer, primary_key=True, index=True)
    muscle_group = Column(String(50))
    last_trained = Column(DateTime)
    volume_last_session = Column(Float)  # Sets x Reps x Weight
    freshness_score = Column(Float, default=100)  # 0-100, decays after training
```

### Step 2.5: Progressive Overload Service (services/progression.py)
```python
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from ..models import Exercise, ExerciseSet, WorkoutSession, PersonalRecord, MuscleRecovery

class ProgressionService:
    """
    Handles progressive overload calculations.
    
    RULES:
    - Compound exercises: +2.5kg when all target reps completed
    - Isolation exercises: +1.25kg when all target reps completed
    - If RPE >= 9: maintain weight (too hard)
    - If failed reps: maintain weight, retry next session
    - After 3 failed sessions: deload 10%
    """
    
    COMPOUND_INCREMENT = 2.5  # kg
    ISOLATION_INCREMENT = 1.25  # kg
    DELOAD_PERCENTAGE = 0.10  # 10% deload after plateau
    PLATEAU_SESSIONS = 3  # Sessions before deload
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_next_weight(
        self, 
        exercise_id: int, 
        target_reps: int,
        last_sessions: int = 5
    ) -> Dict:
        """Calculate recommended weight for next workout."""
        
        exercise = self.db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not exercise:
            return {"error": "Exercise not found"}
        
        # Get last N sessions for this exercise
        recent_sets = (
            self.db.query(ExerciseSet)
            .filter(ExerciseSet.exercise_id == exercise_id)
            .filter(ExerciseSet.is_warmup == False)
            .order_by(ExerciseSet.created_at.desc())
            .limit(last_sessions * 4)  # Assume ~4 sets per session
            .all()
        )
        
        if not recent_sets:
            return {
                "exercise": exercise.name,
                "recommended_weight": 20.0,  # Starting weight
                "reason": "No previous data - start with comfortable weight",
                "progression_status": "new"
            }
        
        # Analyze last session performance
        last_session_sets = recent_sets[:4]  # Most recent 4 sets
        
        avg_reps = sum(s.reps for s in last_session_sets) / len(last_session_sets)
        avg_weight = sum(s.weight for s in last_session_sets) / len(last_session_sets)
        avg_rpe = sum(s.rpe or 7 for s in last_session_sets) / len(last_session_sets)
        
        completed_target = all(s.reps >= target_reps for s in last_session_sets)
        
        # Determine increment based on exercise type
        increment = (
            self.COMPOUND_INCREMENT 
            if exercise.exercise_type == "compound" 
            else self.ISOLATION_INCREMENT
        )
        
        # Decision logic
        if avg_rpe >= 9:
            return {
                "exercise": exercise.name,
                "recommended_weight": round(avg_weight, 2),
                "reason": f"RPE was {avg_rpe:.1f} (high) - maintain weight for adaptation",
                "progression_status": "maintain",
                "last_performance": {"weight": avg_weight, "avg_reps": avg_reps, "avg_rpe": avg_rpe}
            }
        
        if completed_target:
            new_weight = avg_weight + increment
            return {
                "exercise": exercise.name,
                "recommended_weight": round(new_weight, 2),
                "reason": f"Completed {avg_reps:.0f} reps - progressive overload +{increment}kg",
                "progression_status": "increase",
                "last_performance": {"weight": avg_weight, "avg_reps": avg_reps, "avg_rpe": avg_rpe}
            }
        
        # Check for plateau
        failed_sessions = self._count_failed_sessions(exercise_id, target_reps)
        
        if failed_sessions >= self.PLATEAU_SESSIONS:
            new_weight = avg_weight * (1 - self.DELOAD_PERCENTAGE)
            return {
                "exercise": exercise.name,
                "recommended_weight": round(new_weight, 2),
                "reason": f"Plateau detected ({failed_sessions} sessions) - deload {self.DELOAD_PERCENTAGE*100:.0f}%",
                "progression_status": "deload",
                "last_performance": {"weight": avg_weight, "avg_reps": avg_reps, "avg_rpe": avg_rpe}
            }
        
        return {
            "exercise": exercise.name,
            "recommended_weight": round(avg_weight, 2),
            "reason": f"Reps below target ({avg_reps:.0f}/{target_reps}) - retry same weight",
            "progression_status": "retry",
            "last_performance": {"weight": avg_weight, "avg_reps": avg_reps, "avg_rpe": avg_rpe}
        }
    
    def _count_failed_sessions(self, exercise_id: int, target_reps: int) -> int:
        return 0  # Implement counting logic
    
    def calculate_estimated_1rm(self, weight: float, reps: int) -> float:
        """Brzycki formula for estimated 1RM."""
        if reps == 1:
            return weight
        if reps > 12:
            reps = 12
        return weight * (36 / (37 - reps))
    
    def get_muscle_freshness(self, muscle_group: str) -> Dict:
        """Calculate muscle recovery status."""
        recovery = self.db.query(MuscleRecovery).filter(
            MuscleRecovery.muscle_group == muscle_group
        ).first()
        
        if not recovery:
            return {"muscle": muscle_group, "freshness": 100, "days_rest": 999}
        
        days_since = (datetime.utcnow() - recovery.last_trained).days
        freshness_map = {0: 30, 1: 60, 2: 85}
        freshness = freshness_map.get(days_since, 100)
        
        return {
            "muscle": muscle_group,
            "freshness": freshness,
            "days_rest": days_since,
            "recommendation": "ready" if freshness >= 80 else "rest more"
        }
```

### Step 2.6: AI Coach Service (services/ai_coach.py)
```python
import chromadb
from chromadb.config import Settings as ChromaSettings
import ollama
import json
from typing import Dict, List, Optional
from datetime import datetime
from ..config import settings

class AICoachService:
    """
    Phi-3 powered AI coach with ChromaDB memory.
    
    ANTI-HALLUCINATION RULES:
    1. Always query ChromaDB for context BEFORE generating
    2. Force JSON output for structured responses
    3. Validate output against known exercises
    4. Fallback to algorithmic recommendation if AI fails
    """
    
    def __init__(self):
        self.chroma_client = chromadb.PersistentClient(
            path=settings.CHROMADB_PATH,
            settings=ChromaSettings(anonymized_telemetry=False)
        )
        self.workout_collection = self.chroma_client.get_or_create_collection(
            name="workout_history",
            metadata={"description": "Stores workout sessions and AI decisions"}
        )
        self.model = settings.PHI3_MODEL
    
    def store_workout_context(self, session_id: int, workout_data: Dict, notes: str = ""):
        """Store workout in ChromaDB for future context."""
        document = json.dumps({
            "session_id": session_id,
            "date": workout_data.get("date", str(datetime.utcnow())),
            "day_type": workout_data.get("day_type"),
            "exercises": workout_data.get("exercises", []),
            "total_volume": workout_data.get("total_volume"),
            "avg_rpe": workout_data.get("avg_rpe"),
            "notes": notes
        })
        
        self.workout_collection.add(
            documents=[document],
            metadatas=[{
                "session_id": str(session_id),
                "date": workout_data.get("date", str(datetime.utcnow())),
                "day_type": workout_data.get("day_type", "unknown")
            }],
            ids=[f"session_{session_id}"]
        )
    
    def get_relevant_context(self, query: str, n_results: int = 10) -> List[Dict]:
        """Retrieve relevant workout history from ChromaDB."""
        results = self.workout_collection.query(query_texts=[query], n_results=n_results)
        
        contexts = []
        if results and results['documents']:
            for doc in results['documents'][0]:
                try:
                    contexts.append(json.loads(doc))
                except:
                    contexts.append({"raw": doc})
        return contexts
    
    def generate_workout_recommendation(
        self,
        day_number: int,
        priority_muscle: str,
        available_exercises: List[Dict],
        user_preferences: Optional[Dict] = None
    ) -> Dict:
        """Generate AI-powered workout recommendation using RAG pattern."""
        
        # Step 1: Get relevant history
        context_query = f"Day {day_number} {priority_muscle} priority workouts"
        history = self.get_relevant_context(context_query, n_results=8)
        
        # Step 2: Build prompt
        system_prompt = """You are a strength training coach AI. Rules:
1. ONLY use exercises from the provided list
2. NEVER invent exercises or weights
3. Output ONLY valid JSON
4. Base weights on provided history
5. If unsure, maintain previous weight"""

        user_prompt = f"""
Generate workout for Day {day_number} with {priority_muscle} as priority.

AVAILABLE EXERCISES:
{json.dumps(available_exercises, indent=2)}

RECENT HISTORY:
{json.dumps(history, indent=2)}

RULES:
- 50% volume on priority muscle ({priority_muscle})
- 50% on supporting muscles
- 4 sets/exercise, 6-8 reps compounds, 8-12 isolation
- +2.5kg compounds, +1.25kg isolation IF completed all reps
- Include 20min treadmill at end

OUTPUT JSON:
{{
    "day_number": {day_number},
    "priority_muscle": "{priority_muscle}",
    "exercises": [
        {{"name": "...", "sets": 4, "reps": "6-8", "weight_kg": 100, "rest_seconds": 120, "is_priority": true}}
    ],
    "cardio": {{"type": "treadmill", "duration_minutes": 20}},
    "estimated_duration_minutes": 75
}}
"""

        # Step 3: Call Phi-3
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                format="json"
            )
            
            result = json.loads(response['message']['content'])
            
            # Validate exercises
            valid_names = {e['name'].lower() for e in available_exercises}
            for ex in result.get('exercises', []):
                if ex['name'].lower() not in valid_names:
                    raise ValueError(f"Invalid exercise: {ex['name']}")
            
            return {"success": True, "recommendation": result, "source": "ai"}
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "recommendation": self._fallback_recommendation(day_number, priority_muscle, available_exercises),
                "source": "algorithm_fallback"
            }
    
    def _fallback_recommendation(self, day_number: int, priority_muscle: str, exercises: List[Dict]) -> Dict:
        """Algorithmic fallback if AI fails."""
        priority_ex = [e for e in exercises if e.get('muscle_group', '').lower() == priority_muscle.lower()][:3]
        supporting_ex = [e for e in exercises if e.get('muscle_group', '').lower() != priority_muscle.lower()][:3]
        
        workout_exercises = []
        for ex in priority_ex + supporting_ex:
            workout_exercises.append({
                "name": ex['name'],
                "sets": 4,
                "reps": "6-8" if ex.get('exercise_type') == 'compound' else "8-12",
                "weight_kg": ex.get('last_weight', 20),
                "rest_seconds": 120 if ex.get('exercise_type') == 'compound' else 90,
                "is_priority": ex in priority_ex
            })
        
        return {
            "day_number": day_number,
            "priority_muscle": priority_muscle,
            "exercises": workout_exercises,
            "cardio": {"type": "treadmill", "duration_minutes": 20},
            "estimated_duration_minutes": 75
        }
```

---

## PHASE 3: API ENDPOINTS

### main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import workouts, exercises, progress, ai
from .database import engine, Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Workout Tracker", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(workouts.router, prefix="/api/workouts", tags=["Workouts"])
app.include_router(exercises.router, prefix="/api/exercises", tags=["Exercises"])
app.include_router(progress.router, prefix="/api/progress", tags=["Progress"])
app.include_router(ai.router, prefix="/api/ai", tags=["AI Coach"])

@app.get("/")
def root():
    return {"status": "running", "app": "AI Workout Tracker"}
```

### routers/ai.py
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ..database import get_db
from ..services.ai_coach import AICoachService
from ..services.progression import ProgressionService
from ..models import Exercise

router = APIRouter()

class WorkoutRequest(BaseModel):
    day_number: int
    priority_muscle: str
    preferences: Optional[dict] = None

@router.post("/recommend")
def get_ai_recommendation(request: WorkoutRequest, db: Session = Depends(get_db)):
    ai_coach = AICoachService()
    
    exercises = db.query(Exercise).all()
    exercise_list = [
        {"name": e.name, "muscle_group": e.muscle_group, "exercise_type": e.exercise_type}
        for e in exercises
    ]
    
    return ai_coach.generate_workout_recommendation(
        day_number=request.day_number,
        priority_muscle=request.priority_muscle,
        available_exercises=exercise_list,
        user_preferences=request.preferences
    )

@router.get("/next-weight/{exercise_id}")
def get_next_weight(exercise_id: int, target_reps: int = 8, db: Session = Depends(get_db)):
    progression = ProgressionService(db)
    return progression.calculate_next_weight(exercise_id, target_reps)

@router.get("/muscle-status/{muscle_group}")
def get_muscle_status(muscle_group: str, db: Session = Depends(get_db)):
    progression = ProgressionService(db)
    return progression.get_muscle_freshness(muscle_group)
```

---

## PHASE 4: DOCKER SETUP

### docker-compose.yml
```yaml
version: '3.8'

services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: workout
      POSTGRES_PASSWORD: workout123
      POSTGRES_DB: workout_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://workout:workout123@db:5432/workout_db
      CHROMADB_PATH: /app/chromadb_data
      OLLAMA_HOST: http://host.docker.internal:11434
    volumes:
      - chromadb_data:/app/chromadb_data
    depends_on:
      - db
    extra_hosts:
      - "host.docker.internal:host-gateway"

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on:
      - backend

volumes:
  postgres_data:
  chromadb_data:
```

---

## PHASE 5: FRONTEND (Next.js + Tailwind)

### Core Pages
- **/** - Dashboard: today's workout, muscle status, progress
- **/workout/[id]** - Active session with timer, set logging
- **/history** - Past workouts calendar
- **/progress** - Charts (weight, 1RM, volume)
- **/settings** - Plan configuration

### Key Components
- WorkoutCard - displays workout summary
- ExerciseRow - single exercise with sets
- RestTimer - countdown between sets
- ProgressChart - Recharts line graphs
- MuscleStatusGrid - recovery heat map

### Color Palette (Dark Theme)
```
bg-primary: #111827 (gray-900)
bg-secondary: #1F2937 (gray-800)
accent-blue: #3B82F6
accent-green: #10B981
```

---

## PHASE 6: SETUP COMMANDS

```bash
# 1. Find Phi-3 on D: drive
dir D:\ /s /b | findstr -i "phi"

# 2. Ensure Ollama running
ollama serve
ollama list  # verify phi3

# 3. Start services
docker-compose up -d

# 4. Verify
curl http://localhost:8000/health
curl http://localhost:3000
```

---

## SUCCESS CRITERIA
1. Backend starts without errors
2. Frontend connects to API  
3. Phi-3 generates valid recommendations
4. ChromaDB persists history
5. Progressive overload calculates correctly
6. Rest timer works
7. Charts display progress
