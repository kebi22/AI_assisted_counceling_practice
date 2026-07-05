"""Security helpers.

Version 1 uses mock authentication. The ``CurrentUser`` model and helpers here
define the interface so real authentication can be added later without changing
the service or endpoint signatures.
"""

from dataclasses import dataclass

from app.core.constants import UserRole


@dataclass(frozen=True)
class CurrentUser:
    """The authenticated principal for a request.

    ``email`` is the stable key used to resolve the mock user to a database row.
    """

    id: str
    name: str
    role: UserRole
    email: str

    @property
    def is_faculty(self) -> bool:
        return self.role in (UserRole.FACULTY, UserRole.ADMIN)

    @property
    def is_student(self) -> bool:
        return self.role == UserRole.STUDENT


# Demo identities for Version 1 mock authentication. The emails match the seed
# script so the mock users resolve to real database rows.
DEMO_STUDENT_EMAIL = "demo.student@example.edu"
DEMO_FACULTY_EMAIL = "demo.faculty@example.edu"

DEMO_STUDENT = CurrentUser(
    id="student_001",
    name="Demo Student",
    role=UserRole.STUDENT,
    email=DEMO_STUDENT_EMAIL,
)
DEMO_FACULTY = CurrentUser(
    id="faculty_001",
    name="Demo Faculty",
    role=UserRole.FACULTY,
    email=DEMO_FACULTY_EMAIL,
)
