"""A reference state-transition model for decoupled pointer control."""
from dataclasses import dataclass, field

class InvalidTransition(RuntimeError):
    pass

@dataclass
class MouseState:
    x: float = 0.0
    y: float = 0.0
    held: set[str] = field(default_factory=set)
    actions: list[str] = field(default_factory=list)
    down_count: int = 0
    up_count: int = 0

    def press(self, button: str = "left"):
        if button in self.held:
            raise InvalidTransition("button already held")
        self.held.add(button)
        self.down_count += 1
        self.actions.append(f"down:{button}")

    def move(self, x: float, y: float):
        self.x, self.y = float(x), float(y)
        self.actions.append("move")

    def observe(self):
        self.actions.append("observe")
        return {"position": (self.x, self.y), "held": sorted(self.held)}

    def agent_turn_end(self):
        self.actions.append("turn_end")

    def release(self, button: str = "left"):
        if button not in self.held:
            raise InvalidTransition("button not held")
        self.held.remove(button)
        self.up_count += 1
        self.actions.append(f"up:{button}")

    def abort(self):
        for button in sorted(self.held):
            self.release(button)
        self.actions.append("abort")
