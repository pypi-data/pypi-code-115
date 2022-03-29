import sys
import logging

# Create a custom logger
logger = logging.getLogger(__name__)

# Create handlers
handler = logging.StreamHandler(sys.stdout)

# Create formatters and add it to handlers
handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Add handlers to the logger
logger.addHandler(handler)
