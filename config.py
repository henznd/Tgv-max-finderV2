from datetime import datetime, time, timedelta

# API Configuration
SNCF_API_URL = "https://ressources.data.sncf.com/api/explore/v2.1/catalog/datasets/tgvmax/records"
API_LIMIT = 100

# Date Configuration
MIN_DATE = datetime.now().date()
MAX_DATE = MIN_DATE + timedelta(days=30)  # Fenêtre glissante de 30 jours

# Time Configuration
DEFAULT_START_TIME = time(6, 0)
DEFAULT_END_TIME = time(23, 0)

# Search Configuration
DEFAULT_ORIGIN = "PARIS"
MAX_RANGE_DAYS = 30  # Maximum de 30 jours
DEFAULT_RANGE_DAYS = 7  # Une semaine par défaut

# Cache Configuration
CACHE_TTL = 3600  # 1 hour in seconds 