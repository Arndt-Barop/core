"""Constants for the WAGO I/O System integration."""

DOMAIN = "wago_io_system"

# Configuration
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 1  # seconds
DEFAULT_PORT = 502
DEFAULT_TIMEOUT = 5

# Module detection registers
CONFIG_REG_1_64 = 0x2030
CONFIG_REG_65_128 = 0x2031
CONFIG_REG_129_192 = 0x2032
CONFIG_REG_193_255 = 0x2033

# Process image registers
PROCESS_INPUT_START = 0x0000
PROCESS_OUTPUT_START = 0x0200
MAX_PROCESS_IMAGE_SIZE = 256  # Maximum number of registers to read
