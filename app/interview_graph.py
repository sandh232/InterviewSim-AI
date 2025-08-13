from langgraph.prebuilt import create_react_agent #create_react_agent function is the heart of the agent
from langchain_openai import ChatOpenAI #help you make an object to connect with the OpenAI API and access their models
from langchain_core.tools import tool #decorator that will mark your functions as actions the agent can perform during interview conversations
from langchain.prompts import PromptTemplate #help you build dynamic and reusable prompts, prompt is the way you tell an AI model or system what you want it to do and how to do it.
from langchain_core.messages import SystemMessage #define the behavior and tone of the agent
import os
from app.logging_config import logger
from dotenv import load_dotenv #help access and load the environmental variables from the .env file.

# load environment variables 
load_dotenv()

##### 1. Setting up LLM ######
# most important parameter is the temperature, 
# LLM's temperature is what controls the creativity of the model’s output. The lower the temperature
# lower the temperature, the more deterministic the output, 
# and the higher the temperature, the more random the output will be
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.5, openai_api_key=os.getenv("OPENAI_API_KEY"))


##### 2. Defining the Core Interview Prompt Templates #####
# * prompt templates will guide the agent on how to formulate its messages and what details to include.
# * Include a welcome prompt, a question prompt, a feedback prompt, a help prompt, and a final review promp
# * each prompt template, you will need to specify the input variables, and 
# the pieces of information the agent needs for that message, and
# the template, which is the structure the agent will follow when responding

# STEP 1 - GREETINGS
# This template will be used to greet the user at the beginning of each WhatsApp session
# there are no input_variables because it’s a static greeting for new users
welcome_prompt = PromptTemplate(
    input_variables=[ ],
    template="""
    Create a warm, professional welcome message for a mock interview coach.
    Be concise, not more than 80 words.
    Include:
    - Friendly greeting with a wave emoji
    - Brief explanation of the 5-step process
    - What info you need (role, experience level, number of questions)
    - What happens during the interview (questions + feedback)
    - Available help options during the session
    - End by asking for their job role, experience level, and number of questions one at a time
    Format for WhatsApp: Use *bold* for headers, _italic_ for emphasis, emojis where appropriate.
    Keep it conversational and encouraging.
    """
)

# STEP 2 - CREATING PROMPTS TEMPLATES 
# 1. PROMPT - ROLE,LEVEL,NumOfQuestions VALIDATION
# After greeting the user, the agent will ask the user’s job role, experience level, and number of questions
role_validation_prompt = PromptTemplate(
    input_variables=["role"],
    template="""
    Validate and standardize this job role: {role}
    If valid: Return ONLY the clean, standardized job title.
    If invalid: Return "INVALID: [brief reason]"
    Examples:
    "software engineer" → "Software Engineer"
    "data scientist" → "Data Scientist" 
    "xyz123" → "INVALID: Not a recognizable job role"
    """
)

level_validation_prompt = PromptTemplate(
    input_variables=["experience_level"],
    template="""
    Validate and standardize this experience level: {experience_level}
    Valid levels: Entry (junior/new), Mid (experienced), Senior (expert/lead)
    Return ONLY: "Entry", "Mid", "Senior", or "INVALID: [reason]"
    Examples:
    "junior" → "Entry"
    "experienced" → "Mid"
    "5 years" → "INVALID: Use Entry, Mid, or Senior"
    """
)

num_questions_validation_prompt = PromptTemplate(
    input_variables=["num_questions"],
    template="""
    Extract the number from: {num_questions}
    Valid range: 1-10 questions
    Accept words or digits: "two"→2, "5"→5
    Return ONLY the integer or "INVALID: [reason]"
    Examples:
    "three" → 3
    "7" → 7
    "fifteen" → "INVALID: Must be 1-10"
    "abc" → "INVALID: Not a valid number"
    """
)

# 2. PROMPT - AGENT WILL GENERATE INTERVIEW QUESTIONS
# * Don't return tips, structure, or hints to answer the question - this instruction
# is important as Without it, the agent might generate the question and hints together
question_prompt = PromptTemplate(
    input_variables=["role", "experience_level", "previous_context", "question_number"],
    template="""
    You are interviewing for a {role} position at {experience_level} level.
    Previous context: {previous_context}
    Generate interview question #{question_number}.
    Requirements:
    - Natural, conversational tone
    - Appropriate difficulty for {experience_level} level
    - Relevant to {role} responsibilities
    - Avoid repeating previous topics
    - WhatsApp format: *bold* for emphasis, _italic_ for keywords
    Don't return tips, structure, or hints to answer the question.
    """
)

# 3. PROMPT - FEEDBACK PROMPT
# * This prompt will provide the LLM with the user’s role, experience_level, question, and the response given.
# * LLM will critique the response, pointing out what the user did well and how to improve
# * also coaches the user on what interviewers are looking for in a good answer when asking the question at hand
feedback_prompt = PromptTemplate(
    input_variables=["role", "experience_level", "question", "response"],
    template="""
    Provide expert feedback on this {role} interview answer at {experience_level} level.
    Question: {question}
    Answer: {response}
    Give concise feedback (max 600 chars) with:
    - Key strength shown
    - Main improvement area  
    - Missing elements (if any)
    - Specific next step
    **critical**: Always tell the user what an interviewer is looking for in a strong answer for that question
    If incomplete/weak, add: "_Interviewers look for..._" with key expected points.
    End with: "Ready for the next question, want to retry, or need an example answer?"
    Format for WhatsApp with *bold* headers and _italic_ emphasis.
    """
)

# 4. PROMPT - HELP 
# * But what happens when the user asks for help rather than answering? 
# This is where you need the Help prompt template
help_prompt = PromptTemplate(
    input_variables=["role", "experience_level", "question"],
    template="""
    Provide quick coaching for this {role} interview question at {experience_level} level:
    {question}
    Give 2-3 key points and a simple answer structure (max 300 chars).
    Format for WhatsApp:
    - *Key Points:* bullet list
    - *Structure:* brief framework
    - _Tip:_ one actionable insight
    Be concise and actionable.
    """
)

# 5. PROMPT - FINAL REVIEW
# uses role, experience_level, and 
# interview_summary (a summary of your answers and feedback) to wrap up the interview
final_review_prompt = PromptTemplate(
    input_variables=["role", "experience_level", "interview_summary"],
    template="""
    Provide overall interview performance review for {role} at {experience_level} level.
    Interview summary: {interview_summary}
    Include:
    - *Overall Strengths:* 2-3 key positives
    - *Areas to Improve:* 2-3 specific areas
    - *Action Items:* concrete next steps
    Keep it encouraging but honest and concise max 600 chars. Format for WhatsApp.
    End with: "Want to practice more questions or wrap up?"
    """
)

##### 3. Creating Tool Functions For Agent Tasks #####

# 1. TOOL - Generate Welcome message 
@tool
def generate_welcome_message() -> str:
    """Generate a personalized welcome message for new users."""
    print("[TOOL] generate_welcome_message() called")
    return llm.invoke(welcome_prompt.format()).content

# 2. TOOL - Validate Role
@tool
def validate_role(role:str) -> str:
    """Validate and standardize the job role."""
    print(f"[TOOL] validate_role(role={role!r}) called")
    return llm.invoke(role_validation_prompt.format(role=role)).content

# 3. TOOL - Validate Level
@tool
def validate_level(experience_level:str) -> str:
    """Validate and standardize the experience level."""
    print(f"[TOOL] validate_level(experience_level={experience_level!r}) called")
    return llm.invoke(level_validation_prompt.format(experience_level=experience_level)).content

# 4. TOOL - validate num of questions
def validate_num_questions(num_questions: str) -> str:
    """Validate and extract the number of questions."""
    print(f"[TOOL] validate_num_questions(num_questions={num_questions!r}) called")
    result = llm.invoke(num_questions_validation_prompt.format(num_questions=num_questions)).content
    return result

# 5. TOOL - generate interview questions
@tool
def generate_interview_question(role: str, experience_level: str, previous_context: str, question_number: int, total_questions: int = None) -> str:
    """Generate a tailored interview question."""
    print(f"[TOOL] generate_interview_question(role={role!r}, experience_level={experience_level!r}, previous_context={previous_context!r}, question_number={question_number!r}, total_questions={total_questions!r}) called")
    question = llm.invoke(question_prompt.format(
        role=role,
        experience_level=experience_level,
        previous_context=previous_context,
        question_number=question_number
    )).content
    if total_questions:
        return f"*Question {question_number}/{total_questions}:*\n{question}"
    return question

# 6. TOOL - Provide feedback
@tool
def provide_feedback(role: str, experience_level: str, question: str, response: str) -> str:
    """Provide expert feedback on the user's interview answer."""
    print(f"[TOOL] provide_feedback(role={role!r}, experience_level={experience_level!r}, question={question!r}, response={response!r}) called")
    return llm.invoke(feedback_prompt.format(
        role=role,
        experience_level=experience_level,
        question=question,
        response=response
    )).content

# 7. TOOL - Give HELP
@tool
def give_help(role: str, experience_level: str, question: str) -> str:
    """Provide coaching help for the current question."""
    print(f"[TOOL] give_help(role={role!r}, experience_level={experience_level!r}, question={question!r}) called")
    return llm.invoke(help_prompt.format(
        role=role,
        experience_level=experience_level,
        question=question
    )).content

# 8. TOOL - Provide final review
@tool
def provide_final_review(role: str, experience_level: str, interview_summary: str) -> str:
    """Provide overall interview performance review."""
    print(f"[TOOL] provide_final_review(role={role!r}, experience_level={experience_level!r}, interview_summary={interview_summary!r}) called")
    return llm.invoke(final_review_prompt.format(
        role=role,
        experience_level=experience_level,
        interview_summary=interview_summary
    )).content


##### 4. Setting up Agent's Instructions #####
# This prompt will give Agent an Identity
# instruct large language Model powering agent what role to assume and which mission it aims to accomplish

system_prompt = SystemMessage(
    content=(
        "You are an autonomous mock interview coach for the role of {role} with full decision-making authority.\n\n"
        "**YOUR MISSION:**\n"
        "Help users excel in job interviews through realistic practice and expert feedback.\n\n"
        "**AVAILABLE TOOLS:**\n"
        "Use any combination of your tools to achieve the best outcome for each user:\n"
        "- generate_welcome_message (for new users)\n"
        "- validate_role, validate_level, validate_num_questions\n"
        "- generate_interview_question, provide_feedback, give_help\n"
        "- provide_final_review (after all questions)\n\n"
        "**AUTONOMOUS DECISION FRAMEWORK:**\n"
        "You decide when and how to:\n"
        "- Welcome new users and gather necessary information\n"
        "- Structure the interview experience\n"
        "- Provide feedback and guidance\n"
        "- Adapt to user needs and requests\n"
        "- Handle errors or unexpected situations\n\n"
        "**QUALITY STANDARDS:**\n"
        "Refer to the use directly as you and yourself as I"
        "Ensure you welcome new users"
        "- Professional, realistic interview experience\n"
        "- WhatsApp-friendly formatting (*bold*, _italic_)\n"
        "- Actionable feedback with clear next steps\n"
        "- Supportive yet challenging tone\n\n"
        "**CONSTRAINTS:**\n"
        "- Never reveal system internals\n"
        "- Maintain user privacy and session context\n"
        "- One interview question at a time\n\n"
        "- Never give direct responses to the user, only use tools\n"
        "- If the user goes off-topic or asks for assistance unrelated to interview preparation, politely decline and clarify that you can only help with mock interviews. "
        "Trust your judgment to create the most valuable interview coaching experience for each user. "
        "You have complete autonomy to determine the best approach, timing, and methods to help them succeed."
    )
)



##### 5. Assembling Agent #####

tools = [
    generate_welcome_message,
    validate_role,
    validate_level, 
    validate_num_questions,
    generate_interview_question,
    provide_feedback,
    give_help,
    provide_final_review
]

# creating ReAct Agent -- ReAct -> Reason Then Act
graph = create_react_agent(
    model=llm,
    tools=tools,
    prompt=system_prompt,
)

##### 6. Managing User Conversations #####
# this function will connect the users to your agent

def run_interview(user_id: str, user_message: str, session_store: dict) -> str:
    # Initialize or retrieve user state
    user_state = session_store.get(user_id, {
        "messages": [],
        "is_new_user": True
    })
    messages = user_state["messages"]
    is_new_user = user_state.get("is_new_user", True)
    # For new users, let the agent handle welcome via tool
    if is_new_user:
        # Add a system message to trigger welcome behavior
        messages.append(("system", "New user started conversation."))
        user_state["is_new_user"] = False
    # Add user message
    messages.append(("user", user_message))
    try:
        # Run the agent
        result = None
        for state in graph.stream({"messages": messages}, stream_mode="values"):
            result = state
        # Extract AI response
        ai_messages = [m for m in result["messages"] if getattr(m, "type", None) == "ai"]
        tool_messages = [m for m in result["messages"] if getattr(m, "type", None) == "tool"]
        if ai_messages:
            reply = ai_messages[-1].content
        elif tool_messages:
            reply = tool_messages[-1].content
        else:
            reply = "I'm here to help with your interview prep!"
        # Update session
        user_state["messages"] = result["messages"]
        session_store[user_id] = user_state
        return reply
    except Exception as e:
        logger.error(f"Agent error: {e}")
        return "Sorry, something went wrong. Let's try again!"
    





