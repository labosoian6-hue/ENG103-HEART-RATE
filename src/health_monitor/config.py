

# --- I2C / sensor ---
I2C_BUS = 1
MAX30102_ADDRESS = 0x57

# --- GPIO pins (BCM numbering) ---
LED_OK_PIN = 17
LED_ALERT_PIN = 27
BUTTON_PIN = 22

# --- Alert thresholds ---
BPM_LOW = 50
BPM_HIGH = 120
SPO2_LOW = 94

# --- Storage ---
LOCAL_DATA_DIR = "data"
LOCAL_READINGS_FILE = "readings.csv"

# --- Sampling ---
READ_INTERVAL_SECONDS = 1.0
USE_MOCK_SENSOR = True
