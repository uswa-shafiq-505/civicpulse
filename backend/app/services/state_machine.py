from app.models import Status

# Explicit transition table, not an if/elif chain.
VALID_TRANSITIONS: dict[Status, set[Status]] = {
    Status.open: {Status.in_progress, Status.rejected},
    Status.in_progress: {Status.resolved, Status.rejected},
    Status.resolved: set(),
    Status.rejected: set(),
}


class InvalidTransitionError(Exception):
    def __init__(self, current: Status, attempted: Status):
        self.current = current
        self.attempted = attempted
        super().__init__(f"Cannot transition from '{current.value}' to '{attempted.value}'")


def validate_transition(current: Status, attempted: Status) -> None:
    if attempted not in VALID_TRANSITIONS.get(current, set()):
        raise InvalidTransitionError(current, attempted)
