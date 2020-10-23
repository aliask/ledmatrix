# LedFrame dataclass

from dataclasses import dataclass, field

@dataclass
class LedFrame:
  height: int
  width: int
  pixels: list = field(default_factory=list)
