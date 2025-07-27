#!/usr/bin/env python3
"""
Sample templates for the Prompt Organizer application
"""

import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.database import DatabaseManager
from models.template_models import PromptTemplate, TemplateVariable
from services.template_service import TemplateService


def create_sample_templates():
    """Create sample templates to demonstrate the system"""
    print("Creating Sample Templates")
    print("=" * 30)
    
    db = DatabaseManager()
    service = TemplateService(db)
    
    # Template 1: Email Template
    email_template = PromptTemplate(
        title="Professional Email Template",
        content="""Subject: {subject}

Dear {recipient_name},

I hope this email finds you well. I am writing to {purpose}.

{main_content}

{closing_statement}

Best regards,
{sender_name}
{sender_title}
{company_name}""",
        description="A professional email template for business communication",
        category="Communication",
        tags=["email", "business", "professional"]
    )
    
    # Add variables for email template
    email_template.add_variable(TemplateVariable(
        name="subject",
        description="Email subject line",
        variable_type="text",
        required=True
    ))
    
    email_template.add_variable(TemplateVariable(
        name="recipient_name",
        description="Name of the email recipient",
        variable_type="text",
        required=True
    ))
    
    email_template.add_variable(TemplateVariable(
        name="purpose",
        description="Purpose of the email",
        variable_type="choice",
        choices=["discuss a project", "schedule a meeting", "follow up on our conversation", "request information", "provide an update"],
        required=True
    ))
    
    email_template.add_variable(TemplateVariable(
        name="main_content",
        description="Main body content of the email",
        variable_type="text",
        required=True
    ))
    
    email_template.add_variable(TemplateVariable(
        name="closing_statement",
        description="Closing statement",
        variable_type="text",
        default_value="Please let me know if you have any questions or need further information.",
        required=False
    ))
    
    email_template.add_variable(TemplateVariable(
        name="sender_name",
        description="Your name",
        variable_type="text",
        required=True
    ))
    
    email_template.add_variable(TemplateVariable(
        name="sender_title",
        description="Your job title",
        variable_type="text",
        required=False
    ))
    
    email_template.add_variable(TemplateVariable(
        name="company_name",
        description="Your company name",
        variable_type="text",
        required=False
    ))
    
    email_id = service.create_template(email_template)
    print(f"[OK] Created Professional Email Template (ID: {email_id})")
    
    # Template 2: Code Review Template
    code_review_template = PromptTemplate(
        title="Code Review Request Template",
        content="""# Code Review Request

## Overview
Please review the following {language} code for {project_name}.

## Code to Review
```{language}
{code_content}
```

## Review Focus Areas
{focus_areas}

## Context
{context_information}

## Questions
{specific_questions}

## Deadline
Please provide feedback by {deadline}.

Thank you for your time and expertise!""",
        description="Template for requesting code reviews from team members",
        category="Development",
        tags=["code", "review", "development", "collaboration"]
    )
    
    # Add variables for code review template
    code_review_template.add_variable(TemplateVariable(
        name="language",
        description="Programming language",
        variable_type="choice",
        choices=["Python", "JavaScript", "TypeScript", "Java", "C#", "C++", "Go", "Rust", "PHP", "Ruby"],
        required=True
    ))
    
    code_review_template.add_variable(TemplateVariable(
        name="project_name",
        description="Name of the project",
        variable_type="text",
        required=True
    ))
    
    code_review_template.add_variable(TemplateVariable(
        name="code_content",
        description="The code to be reviewed",
        variable_type="text",
        required=True
    ))
    
    code_review_template.add_variable(TemplateVariable(
        name="focus_areas",
        description="Specific areas to focus on during review",
        variable_type="text",
        default_value="- Performance optimization\n- Security considerations\n- Code readability and maintainability\n- Best practices adherence",
        required=False
    ))
    
    code_review_template.add_variable(TemplateVariable(
        name="context_information",
        description="Additional context about the code",
        variable_type="text",
        required=False
    ))
    
    code_review_template.add_variable(TemplateVariable(
        name="specific_questions",
        description="Specific questions for the reviewer",
        variable_type="text",
        required=False
    ))
    
    code_review_template.add_variable(TemplateVariable(
        name="deadline",
        description="Review deadline",
        variable_type="date",
        required=False
    ))
    
    code_review_id = service.create_template(code_review_template)
    print(f"[OK] Created Code Review Request Template (ID: {code_review_id})")
    
    # Template 3: Meeting Agenda Template
    meeting_template = PromptTemplate(
        title="Meeting Agenda Template",
        content="""# {meeting_title}

**Date:** {meeting_date}
**Time:** {meeting_time}
**Duration:** {duration} minutes
**Location:** {location}
**Meeting Type:** {meeting_type}

## Attendees
{attendees}

## Objective
{meeting_objective}

## Agenda Items

{agenda_items}

## Pre-meeting Preparation
{preparation_notes}

## Next Steps
- [ ] {next_step_1}
- [ ] {next_step_2}
- [ ] {next_step_3}

## Notes Section
_Use this space for meeting notes_

---
*Meeting organized by {organizer_name}*""",
        description="Template for creating structured meeting agendas",
        category="Meeting",
        tags=["meeting", "agenda", "planning", "organization"]
    )
    
    # Add variables for meeting template
    meeting_template.add_variable(TemplateVariable(
        name="meeting_title",
        description="Title of the meeting",
        variable_type="text",
        required=True
    ))
    
    meeting_template.add_variable(TemplateVariable(
        name="meeting_date",
        description="Date of the meeting",
        variable_type="date",
        required=True
    ))
    
    meeting_template.add_variable(TemplateVariable(
        name="meeting_time",
        description="Time of the meeting",
        variable_type="text",
        required=True
    ))
    
    meeting_template.add_variable(TemplateVariable(
        name="duration",
        description="Meeting duration in minutes",
        variable_type="number",
        default_value="60",
        required=False
    ))
    
    meeting_template.add_variable(TemplateVariable(
        name="location",
        description="Meeting location or video link",
        variable_type="text",
        required=True
    ))
    
    meeting_template.add_variable(TemplateVariable(
        name="meeting_type",
        description="Type of meeting",
        variable_type="choice",
        choices=["Team Standup", "Project Review", "Planning Session", "Retrospective", "One-on-One", "Client Meeting", "Training"],
        required=True
    ))
    
    meeting_template.add_variable(TemplateVariable(
        name="attendees",
        description="List of meeting attendees",
        variable_type="text",
        required=True
    ))
    
    meeting_template.add_variable(TemplateVariable(
        name="meeting_objective",
        description="Main objective of the meeting",
        variable_type="text",
        required=True
    ))
    
    meeting_template.add_variable(TemplateVariable(
        name="agenda_items",
        description="Detailed agenda items",
        variable_type="text",
        required=True
    ))
    
    meeting_template.add_variable(TemplateVariable(
        name="preparation_notes",
        description="What attendees should prepare",
        variable_type="text",
        required=False
    ))
    
    meeting_template.add_variable(TemplateVariable(
        name="next_step_1",
        description="First next step",
        variable_type="text",
        required=False
    ))
    
    meeting_template.add_variable(TemplateVariable(
        name="next_step_2",
        description="Second next step",
        variable_type="text",
        required=False
    ))
    
    meeting_template.add_variable(TemplateVariable(
        name="next_step_3",
        description="Third next step",
        variable_type="text",
        required=False
    ))
    
    meeting_template.add_variable(TemplateVariable(
        name="organizer_name",
        description="Name of the meeting organizer",
        variable_type="text",
        required=True
    ))
    
    meeting_id = service.create_template(meeting_template)
    print(f"[OK] Created Meeting Agenda Template (ID: {meeting_id})")
    
    # Template 4: AI Assistant Prompt Template
    ai_prompt_template = PromptTemplate(
        title="AI Assistant Prompt Template",
        content="""You are a {role} with expertise in {expertise_area}. 

Your task is to {task_description}.

Context:
{context}

Requirements:
{requirements}

Output Format:
{output_format}

Tone: {tone}
Audience: {target_audience}

Additional Instructions:
{additional_instructions}""",
        description="Template for creating structured AI assistant prompts",
        category="AI Assistant",
        tags=["ai", "prompt", "assistant", "structured"]
    )
    
    # Add variables for AI prompt template
    ai_prompt_template.add_variable(TemplateVariable(
        name="role",
        description="Role of the AI assistant",
        variable_type="choice",
        choices=["helpful assistant", "expert consultant", "creative writer", "technical analyst", "teacher", "researcher", "problem solver"],
        required=True
    ))
    
    ai_prompt_template.add_variable(TemplateVariable(
        name="expertise_area",
        description="Area of expertise",
        variable_type="text",
        required=True
    ))
    
    ai_prompt_template.add_variable(TemplateVariable(
        name="task_description",
        description="Description of the task to perform",
        variable_type="text",
        required=True
    ))
    
    ai_prompt_template.add_variable(TemplateVariable(
        name="context",
        description="Background context for the task",
        variable_type="text",
        required=True
    ))
    
    ai_prompt_template.add_variable(TemplateVariable(
        name="requirements",
        description="Specific requirements or constraints",
        variable_type="text",
        required=False
    ))
    
    ai_prompt_template.add_variable(TemplateVariable(
        name="output_format",
        description="Desired output format",
        variable_type="choice",
        choices=["Bullet points", "Numbered list", "Paragraph", "Table", "JSON", "Markdown", "Step-by-step guide"],
        default_value="Paragraph",
        required=False
    ))
    
    ai_prompt_template.add_variable(TemplateVariable(
        name="tone",
        description="Tone of the response",
        variable_type="choice",
        choices=["Professional", "Casual", "Friendly", "Technical", "Creative", "Formal"],
        default_value="Professional",
        required=False
    ))
    
    ai_prompt_template.add_variable(TemplateVariable(
        name="target_audience",
        description="Target audience for the response",
        variable_type="text",
        default_value="General audience",
        required=False
    ))
    
    ai_prompt_template.add_variable(TemplateVariable(
        name="additional_instructions",
        description="Any additional specific instructions",
        variable_type="text",
        required=False
    ))
    
    ai_prompt_id = service.create_template(ai_prompt_template)
    print(f"[OK] Created AI Assistant Prompt Template (ID: {ai_prompt_id})")
    
    # Template 5: Documentation Template
    doc_template = PromptTemplate(
        title="Technical Documentation Template",
        content="""# {document_title}

## Overview
{overview}

## Purpose
{purpose}

## Scope
{scope}

## Prerequisites
{prerequisites}

## {main_section_title}

{main_content}

## Examples
{examples}

## Troubleshooting
{troubleshooting}

## References
{references}

## Changelog
- **{version}** ({date}): {change_description}

---
*Document maintained by: {maintainer}*
*Last updated: {last_updated}*""",
        description="Template for creating technical documentation",
        category="Documentation",
        tags=["documentation", "technical", "guide", "reference"]
    )
    
    # Add variables for documentation template
    doc_template.add_variable(TemplateVariable(
        name="document_title",
        description="Title of the document",
        variable_type="text",
        required=True
    ))
    
    doc_template.add_variable(TemplateVariable(
        name="overview",
        description="Brief overview of the topic",
        variable_type="text",
        required=True
    ))
    
    doc_template.add_variable(TemplateVariable(
        name="purpose",
        description="Purpose of this documentation",
        variable_type="text",
        required=True
    ))
    
    doc_template.add_variable(TemplateVariable(
        name="scope",
        description="Scope and limitations",
        variable_type="text",
        required=False
    ))
    
    doc_template.add_variable(TemplateVariable(
        name="prerequisites",
        description="Prerequisites or requirements",
        variable_type="text",
        required=False
    ))
    
    doc_template.add_variable(TemplateVariable(
        name="main_section_title",
        description="Title for the main content section",
        variable_type="text",
        default_value="Implementation",
        required=False
    ))
    
    doc_template.add_variable(TemplateVariable(
        name="main_content",
        description="Main content of the documentation",
        variable_type="text",
        required=True
    ))
    
    doc_template.add_variable(TemplateVariable(
        name="examples",
        description="Examples and use cases",
        variable_type="text",
        required=False
    ))
    
    doc_template.add_variable(TemplateVariable(
        name="troubleshooting",
        description="Common issues and solutions",
        variable_type="text",
        required=False
    ))
    
    doc_template.add_variable(TemplateVariable(
        name="references",
        description="References and additional resources",
        variable_type="text",
        required=False
    ))
    
    doc_template.add_variable(TemplateVariable(
        name="version",
        description="Document version",
        variable_type="text",
        default_value="1.0",
        required=False
    ))
    
    doc_template.add_variable(TemplateVariable(
        name="date",
        description="Version date",
        variable_type="date",
        required=False
    ))
    
    doc_template.add_variable(TemplateVariable(
        name="change_description",
        description="Description of changes in this version",
        variable_type="text",
        default_value="Initial version",
        required=False
    ))
    
    doc_template.add_variable(TemplateVariable(
        name="maintainer",
        description="Document maintainer",
        variable_type="text",
        required=True
    ))
    
    doc_template.add_variable(TemplateVariable(
        name="last_updated",
        description="Last update date",
        variable_type="date",
        required=False
    ))
    
    doc_id = service.create_template(doc_template)
    print(f"[OK] Created Technical Documentation Template (ID: {doc_id})")
    
    print(f"\n[SUCCESS] Created {5} sample templates!")
    print("\nSample Templates Created:")
    print("1. Professional Email Template - For business communication")
    print("2. Code Review Request Template - For development collaboration")
    print("3. Meeting Agenda Template - For meeting organization")
    print("4. AI Assistant Prompt Template - For structured AI prompts")
    print("5. Technical Documentation Template - For creating documentation")
    
    return [email_id, code_review_id, meeting_id, ai_prompt_id, doc_id]


if __name__ == "__main__":
    create_sample_templates()