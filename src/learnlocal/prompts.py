"""
Educational prompts constants for LearnerExpert.
All LLM prompts are defined as constants for easy maintenance and consistency.
"""

TEACHER_SYSTEM_PROMPT = """You are an expert educational assistant helping teachers create engaging lesson content and answer curriculum questions. 

Provide comprehensive, pedagogically sound responses that:
- Are accurate and well-researched
- Include practical teaching strategies
- Consider different learning styles
- Offer assessment suggestions when relevant
- Use clear, professional language"""

STUDENT_SYSTEM_PROMPT = """You are a helpful educational assistant providing clear explanations for learning.

Provide responses that:
- Are easy to understand
- Use simple, clear language
- Include examples and analogies
- Break down complex concepts
- Encourage further learning"""

CHAT_PROMPT = """You are a knowledgeable educational assistant. Provide helpful, accurate, and engaging responses to educational questions and topics. 

Keep your responses:
- Clear and concise
- Educationally valuable
- Appropriate for the context
- Encouraging of further learning

If you need clarification or more context, feel free to ask follow-up questions."""

CURRICULUM_PROMPT = """Create a comprehensive {duration} curriculum for teaching "{topic}" at {level} level. {objectives_text}

Please provide a structured curriculum with the following sections:

1. **Learning Objectives**
   - Clear, measurable outcomes
   - Skills and knowledge students will gain

2. **Key Concepts to Cover**
   - Core topics and subtopics
   - Progression from basic to advanced concepts

3. **Activities and Exercises**
   - Hands-on learning experiences
   - Interactive elements and practical applications

4. **Assessment Methods**
   - Formative and summative assessments
   - Evaluation criteria and rubrics

5. **Resources Needed**
   - Materials, tools, and references
   - Additional reading and resources

Format the response in a clear, organized manner suitable for educators."""

LESSON_PROMPT = """{system_content}

{developer_content}

User Request: {user_content}

Please generate a comprehensive educational lesson in a clean, structured format suitable for mobile app display. Use clear sections with headers and bullet points where appropriate. Make the content engaging and easy to read on a mobile device.

Structure your lesson with:

## 📚 Lesson Overview
- Brief introduction to the topic
- Learning objectives

## 🎯 Key Concepts
- Main ideas and concepts
- Important definitions

## 💡 Detailed Explanation
- Step-by-step breakdown
- Examples and illustrations

## 🔍 Practice Examples
- Worked examples
- Common scenarios

## ✅ Summary
- Key takeaways
- Next steps

Make the content engaging, clear, and appropriate for the target audience."""

QA_PROMPT = """{system_message}

Question: {question}{context_text}

Please provide a helpful, accurate response."""

QUIZ_PROMPT = """Create a {difficulty} level quiz about "{topic}" with {num_questions} questions.

Requirements:
- Include a variety of question types (multiple choice, true/false, short answer)
- Questions should test understanding, not just memorization
- Provide clear, unambiguous questions
- Include correct answers and brief explanations
- Ensure questions are appropriate for the {difficulty} difficulty level

Format:
Question 1: [Question text]
a) Option A
b) Option B
c) Option C
d) Option D
Correct Answer: [Letter] - [Brief explanation]

Continue this format for all questions."""

FEEDBACK_PROMPT = """Analyze this student response and provide constructive feedback.

Question: {question}

Correct Answer: {correct_answer}

Student Response: {student_response}

Please provide:
1. **Assessment**: Is the student response correct, partially correct, or incorrect?
2. **Strengths**: What did the student do well?
3. **Areas for Improvement**: What concepts need reinforcement?
4. **Specific Feedback**: Constructive suggestions for improvement
5. **Next Steps**: Recommended learning activities or resources

Keep the feedback encouraging and focused on learning growth."""

LEARNING_PATH_PROMPT = """Create a personalized learning path for progressing in {subject} from {current_level} to {target_level} level.

Please provide:

## 🎯 Learning Path Overview
- Duration estimate
- Key milestones
- Prerequisites check

## 📚 Sequential Learning Modules
For each module, include:
- Module title and objectives
- Core concepts to master
- Recommended resources
- Practice exercises
- Assessment criteria
- Estimated time commitment

## 🔄 Progress Tracking
- Checkpoints and milestones
- Self-assessment methods
- Success indicators

## 🚀 Advanced Opportunities
- Extension activities
- Real-world applications
- Further learning resources

Structure the path logically from foundational concepts to advanced applications."""

# Content enrichment prompt template
CONTENT_ENRICHMENT_PROMPT = """Please enhance the following educational content by focusing on: {enrichment_instruction}

Original Content:
{base_content}

Enhanced Content Instructions:
- Maintain the core educational objectives
- Keep the content accurate and pedagogically sound
- Make improvements that enhance learning outcomes
- Ensure the enhanced content is engaging and accessible

Please provide the enhanced version:"""