"""
Pydantic models for data validation.
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
import re
import config


class Speaker(BaseModel):
    """Speaker data model with validation."""
    model_config = ConfigDict(validate_assignment=True, extra='forbid')
    
    name: str = Field(..., min_length=config.MIN_NAME_LENGTH, max_length=100)
    title: str = Field(..., min_length=config.MIN_TITLE_LENGTH, max_length=200)
    company: str = Field(..., min_length=config.MIN_COMPANY_LENGTH, max_length=100)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate speaker name."""
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        
        # Remove extra whitespace
        v = ' '.join(v.split())
        
        # Basic validation - just check it's not empty and has reasonable length
        if len(v) < 2:
            raise ValueError('Name too short')
        
        return v.strip()
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Validate job title."""
        if not v or not v.strip():
            raise ValueError('Title cannot be empty')
        
        # Remove extra whitespace
        v = ' '.join(v.split())
        
        return v.strip()
    
    @field_validator('company')
    @classmethod
    def validate_company(cls, v):
        """Validate company name."""
        if not v or not v.strip():
            raise ValueError('Company cannot be empty')
        
        # Remove extra whitespace
        v = ' '.join(v.split())
        
        return v.strip()


class EmailContent(BaseModel):
    """Email content model with validation."""
    model_config = ConfigDict(validate_assignment=True, extra='forbid')
    
    subject: str = Field(..., max_length=config.EMAIL_SUBJECT_MAX_LENGTH)
    body: str = Field(..., max_length=config.EMAIL_BODY_MAX_LENGTH)
    
    @field_validator('subject')
    @classmethod
    def validate_subject(cls, v):
        """Validate email subject."""
        if not v or not v.strip():
            raise ValueError('Email subject cannot be empty')
        
        return v.strip()
    
    @field_validator('body')
    @classmethod
    def validate_body(cls, v):
        """Validate email body."""
        if not v or not v.strip():
            raise ValueError('Email body cannot be empty')
        
        return v.strip()


class ProcessedSpeaker(BaseModel):
    """Processed speaker with email content."""
    model_config = ConfigDict(validate_assignment=True, extra='forbid')
    
    speaker_name: str = Field(..., min_length=config.MIN_NAME_LENGTH, max_length=100)
    speaker_title: str = Field(..., min_length=config.MIN_TITLE_LENGTH, max_length=100)
    speaker_company: str = Field(..., min_length=config.MIN_COMPANY_LENGTH, max_length=100)
    company_category: str = Field(..., pattern=r"^(Builder|Owner|Competitor|Partner|Other)$")
    email_subject: str = Field(..., max_length=config.EMAIL_SUBJECT_MAX_LENGTH)
    email_body: str = Field(..., max_length=config.EMAIL_BODY_MAX_LENGTH)
    
    @field_validator('company_category')
    @classmethod
    def validate_category(cls, v):
        """Validate company category."""
        valid_categories = ["Builder", "Owner", "Competitor", "Partner", "Other"]
        if v not in valid_categories:
            raise ValueError(f'Invalid category: {v}. Must be one of {valid_categories}')
        return v
