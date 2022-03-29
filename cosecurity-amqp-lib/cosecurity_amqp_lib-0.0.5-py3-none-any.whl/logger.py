import logging

# Create a custom logger
logger = logging.getLogger(__name__)

# Create handlers
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)

# Create formatters and add it to handlers
format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(format)

# Add handlers to the logger
logger.addHandler(handler)
