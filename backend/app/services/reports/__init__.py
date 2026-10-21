"""Investigation workspace and report generator services."""

from app.services.reports.generator import ReportGeneratorService
from app.services.reports.investigation import InvestigationService

__all__ = ["InvestigationService", "ReportGeneratorService"]
