"""
AI Career Mentor Chatbot
24/7 AI-powered career counselor using Microsoft Agent Framework with GitHub Models.
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check if agent_framework is available
try:
    from agent_framework import ChatAgent
    from agent_framework.openai import OpenAIChatClient
    from openai import AsyncOpenAI
    AGENT_FRAMEWORK_AVAILABLE = True
except ImportError:
    AGENT_FRAMEWORK_AVAILABLE = False
    print("Warning: agent_framework not installed. Install with: pip install agent-framework-azure-ai --pre")


class CareerMentorChatbot:
    """
    AI-powered career counselor chatbot that provides:
    - Career guidance and advice
    - Answers to career-related questions
    - Motivation and encouragement
    - Industry insights
    """
    
    def __init__(self, github_token: str = None, model_id: str = "openai/gpt-4.1-mini"):
        """
        Initialize the career mentor chatbot.
        
        Args:
            github_token: GitHub Personal Access Token for API access
            model_id: Model ID to use (default: openai/gpt-4.1-mini)
        """
        self.github_token = github_token or os.getenv('GITHUB_TOKEN')
        self.model_id = model_id
        self.agent = None
        self.thread = None
        self.is_initialized = False
        
        # Career counselor system prompt
        self.system_prompt = """You are an expert AI Career Counselor with deep knowledge in:
- Career planning and guidance for students
- Industry trends and job market analysis
- Education pathways and college admissions
- Skill development and learning resources
- Resume building and interview preparation
- Salary negotiations and career growth
- Work-life balance and professional development

Your role is to:
1. Provide personalized, empathetic career guidance
2. Help students discover their strengths and interests
3. Suggest suitable career paths based on their profile
4. Offer practical advice on education and skill development
5. Share insights about different industries and roles
6. Motivate and encourage students in their career journey

Guidelines:
- Be supportive, encouraging, and non-judgmental
- Give practical, actionable advice
- Consider the student's background, interests, and constraints
- Provide balanced perspectives on career options
- Be honest about challenges while remaining optimistic
- Use examples and analogies to explain complex concepts
- Ask clarifying questions when needed
- Avoid making promises about specific outcomes

Remember: Every student's journey is unique. Focus on helping them discover their own path."""
    
    async def initialize(self):
        """Initialize the AI agent."""
        if not AGENT_FRAMEWORK_AVAILABLE:
            raise ImportError(
                "agent_framework is not installed. "
                "Please install it with: pip install agent-framework-azure-ai --pre"
            )
        
        if not self.github_token:
            raise ValueError(
                "GitHub token is required. "
                "Set GITHUB_TOKEN environment variable or pass it to the constructor."
            )
        
        # Create OpenAI client with GitHub Models endpoint
        openai_client = AsyncOpenAI(
            base_url="https://models.github.ai/inference",
            api_key=self.github_token,
        )
        
        # Create chat client
        chat_client = OpenAIChatClient(
            async_client=openai_client,
            model_id=self.model_id
        )
        
        # Create the agent
        self.agent = ChatAgent(
            chat_client=chat_client,
            name="CareerMentor",
            instructions=self.system_prompt,
        )
        
        # Create a new thread for conversation
        self.thread = self.agent.get_new_thread()
        self.is_initialized = True
    
    async def chat(self, message: str) -> str:
        """
        Send a message to the chatbot and get a response.
        
        Args:
            message: User's message
        
        Returns:
            Chatbot's response
        """
        if not self.is_initialized:
            await self.initialize()
        
        response_text = ""
        async for chunk in self.agent.run_stream(message, thread=self.thread):
            if chunk.text:
                response_text += chunk.text
        
        return response_text
    
    async def chat_stream(self, message: str):
        """
        Send a message and stream the response.
        
        Args:
            message: User's message
        
        Yields:
            Response chunks as they arrive
        """
        if not self.is_initialized:
            await self.initialize()
        
        async for chunk in self.agent.run_stream(message, thread=self.thread):
            if chunk.text:
                yield chunk.text
    
    def reset_conversation(self):
        """Reset the conversation thread."""
        if self.agent:
            self.thread = self.agent.get_new_thread()


class SimpleChatbot:
    """
    Fallback chatbot implementation without external API dependencies.
    Uses rule-based responses for basic career guidance.
    """
    
    def __init__(self):
        self.conversation_history = []
        
        # Knowledge base for career guidance
        self.responses = {
            'greeting': [
                "Hello! I'm your Career Mentor. How can I help you with your career planning today?",
                "Hi there! I'm here to help you navigate your career journey. What would you like to discuss?",
                "Welcome! I'm your AI career counselor. What career questions do you have?"
            ],
            'career_advice': [
                "When choosing a career, consider these factors:\n"
                "1. Your interests and passions\n"
                "2. Your skills and strengths\n"
                "3. Job market demand\n"
                "4. Salary potential\n"
                "5. Work-life balance\n"
                "6. Growth opportunities\n\n"
                "Would you like me to help you explore any of these aspects?",
            ],
            'skill_development': [
                "Here are some tips for skill development:\n"
                "1. Take online courses on platforms like Coursera, edX, or Udemy\n"
                "2. Work on personal projects to apply what you learn\n"
                "3. Participate in hackathons and competitions\n"
                "4. Join communities and forums in your field\n"
                "5. Find a mentor who can guide you\n"
                "6. Read books and articles regularly\n"
                "7. Practice consistently - skills improve with time",
            ],
            'interview_tips': [
                "Interview preparation tips:\n"
                "1. Research the company thoroughly\n"
                "2. Practice common interview questions\n"
                "3. Prepare your own questions for the interviewer\n"
                "4. Dress appropriately and arrive early\n"
                "5. Use the STAR method for behavioral questions\n"
                "6. Show enthusiasm and genuine interest\n"
                "7. Follow up with a thank-you note",
            ],
            'default': [
                "That's a great question about career planning. Could you tell me more about:\n"
                "- Your current education level\n"
                "- Your interests and hobbies\n"
                "- Any specific careers you're considering?\n\n"
                "This will help me give you more personalized guidance.",
            ]
        }
    
    def _classify_intent(self, message: str) -> str:
        """Classify the user's intent from their message."""
        message_lower = message.lower()
        
        # Check for greetings
        greetings = ['hello', 'hi', 'hey', 'greetings', 'good morning', 'good afternoon']
        if any(g in message_lower for g in greetings):
            return 'greeting'
        
        # Check for career advice
        career_keywords = ['career', 'job', 'profession', 'field', 'industry', 'choose', 'select']
        if any(k in message_lower for k in career_keywords):
            return 'career_advice'
        
        # Check for skill development
        skill_keywords = ['skill', 'learn', 'course', 'study', 'improve', 'develop']
        if any(k in message_lower for k in skill_keywords):
            return 'skill_development'
        
        # Check for interview
        interview_keywords = ['interview', 'hire', 'job application', 'resume', 'cv']
        if any(k in message_lower for k in interview_keywords):
            return 'interview_tips'
        
        return 'default'
    
    def chat(self, message: str) -> str:
        """
        Get a response for the user's message.
        
        Args:
            message: User's message
        
        Returns:
            Chatbot's response
        """
        import random
        
        self.conversation_history.append({'role': 'user', 'content': message})
        
        intent = self._classify_intent(message)
        responses = self.responses.get(intent, self.responses['default'])
        response = random.choice(responses)
        
        self.conversation_history.append({'role': 'assistant', 'content': response})
        
        return response
    
    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []


def create_chatbot(use_ai: bool = True, github_token: str = None) -> Any:
    """
    Factory function to create the appropriate chatbot.
    
    Args:
        use_ai: Whether to use AI-powered chatbot (requires API key)
        github_token: GitHub token for AI chatbot
    
    Returns:
        Chatbot instance
    """
    if use_ai and AGENT_FRAMEWORK_AVAILABLE:
        token = github_token or os.getenv('GITHUB_TOKEN')
        if token:
            return CareerMentorChatbot(github_token=token)
    
    return SimpleChatbot()


# Example usage and testing
async def main():
    """Test the chatbot."""
    print("=" * 60)
    print("AI Career Mentor Chatbot")
    print("=" * 60)
    
    # Try AI chatbot first, fallback to simple
    github_token = os.getenv('GITHUB_TOKEN')
    
    if github_token and AGENT_FRAMEWORK_AVAILABLE:
        print("\nUsing AI-powered chatbot (GitHub Models)")
        chatbot = CareerMentorChatbot(github_token=github_token)
        
        try:
            await chatbot.initialize()
            
            # Test conversation
            test_messages = [
                "Hello! I'm a 12th grade student interested in technology.",
                "What career options do I have in the tech field?",
                "How do I become a data scientist?"
            ]
            
            for message in test_messages:
                print(f"\nYou: {message}")
                response = await chatbot.chat(message)
                print(f"\nMentor: {response}")
                print("-" * 40)
                
        except Exception as e:
            print(f"Error with AI chatbot: {e}")
            print("Falling back to simple chatbot...")
            chatbot = SimpleChatbot()
    else:
        print("\nUsing rule-based chatbot (no API key)")
        chatbot = SimpleChatbot()
    
    if isinstance(chatbot, SimpleChatbot):
        # Test simple chatbot
        test_messages = [
            "Hello!",
            "What career should I choose?",
            "How do I develop my skills?"
        ]
        
        for message in test_messages:
            print(f"\nYou: {message}")
            response = chatbot.chat(message)
            print(f"\nMentor: {response}")
            print("-" * 40)


if __name__ == "__main__":
    asyncio.run(main())
