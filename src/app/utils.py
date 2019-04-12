# External imports
import logging


# Singleton decorator for the Logger
def singleton(cls):
	instances = {}

	def get_instance():
		if cls not in instances:
			instances[cls] = cls()
		return instances[cls]
	return get_instance()

# Logger class
@singleton
class Logger():

	def __init__(self):
		# Initialize the logger
		self.logger = logging.getLogger('oauth-sidecar')

		# Disable propagation
		self.logger.propagate = False

		# Level set to WARN 
		self.logger.setLevel(logging.WARN)

		# Create a file for logging purposes under /usr/local/googleauth-sidecar/logs/oauth-sidecar.log
		self.handler = logging.FileHandler('/usr/local/googleauth-sidecar/logs/oauth-sidecar.log')

		# Define the formatter
		self.formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

		# Set the formatter for the handler
		self.handler.setFormatter(self.formatter)

		# Add the handler to the logger
		self.logger.addHandler(self.handler)
