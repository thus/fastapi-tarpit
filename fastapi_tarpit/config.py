import logging
from typing import Optional


class TarpitConfig():
    def __init__(
            self: "TarpitConfig",
            interval: int = 2,
            output_length_min: int = 1,
            output_length_max: int = 5,
            logger: Optional[logging.Logger] = None
    ) -> None:
        self.interval: int = interval
        self.output_length_min: int = output_length_min
        self.output_length_max: int = output_length_max
        self.logger = logger if logger else logging.getLogger(__name__)
