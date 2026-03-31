from app.schemas.user import (
    User, UserCreate, UserUpdate, UserInDB, UserWithDetails,
    Token, TokenPayload,
    Skill, SkillCreate,
    PerformanceMetricOut,
)
from app.schemas.chat import (
    ChatRequest, ChatResponse,
    Conversation, ConversationWithMessages, Message,
)
from app.schemas.task import (
    Task, TaskCreate, TaskUpdate, TaskWithLogs,
    TaskAssign, TaskStatusUpdate, TaskLogOut,
    CandidateScore, AIAssignmentResult,
    PlannedTask, ProjectPlan,
)
from app.schemas.document import DocumentResponse
from app.schemas.report import DashboardReport, UserReport
