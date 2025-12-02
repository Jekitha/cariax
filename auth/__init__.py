"""Authentication module for Career Guidance System."""

# Lazy imports to avoid initialization issues
def get_auth_models():
    from auth.models import User, Session, AssessmentResult, init_database
    return User, Session, AssessmentResult, init_database

__all__ = ['get_auth_models']
