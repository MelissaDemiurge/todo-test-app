from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Centralized extensions to avoid circular imports
limiter = Limiter(get_remote_address, default_limits=[])


