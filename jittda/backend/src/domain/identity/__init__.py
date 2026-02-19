"""
Identity Resolution 도메인 패키지

공개 API: models, ports, linkedin_models, linkedin_normalizer 전체를 여기서 re-export.
"""
from domain.identity.linkedin_models import (
    LinkedInCertification,
    LinkedInEducation,
    LinkedInExperience,
    LinkedInProfile,
    LinkedInSkill,
)
from domain.identity.linkedin_normalizer import normalize_linkedin_profile
from domain.identity.models import (
    BlameLineAttribution,
    ConfidenceLevel,
    GitAuthor,
    GitHubProfile,
    IdentityCluster,
    MailmapEntry,
    PureContribution,
)
from domain.identity.ports import GitAuthorReader, GitHubProfileFetcher

__all__ = [
    # models
    "ConfidenceLevel",
    "GitAuthor",
    "GitHubProfile",
    "MailmapEntry",
    "IdentityCluster",
    "BlameLineAttribution",
    "PureContribution",
    # linkedin models
    "LinkedInExperience",
    "LinkedInEducation",
    "LinkedInSkill",
    "LinkedInCertification",
    "LinkedInProfile",
    # linkedin normalizer
    "normalize_linkedin_profile",
    # ports
    "GitAuthorReader",
    "GitHubProfileFetcher",
]
