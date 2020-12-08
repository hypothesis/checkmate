"""Background worker task definitions."""

# Retry policies which can be used as any of:
#   * Transport options for connections
#   * Transport options for celery
#   * Retry policy for queueing messages
#   * Retry policy for delaying tasks


RETRY_POLICY_QUICK = {
    "max_retries": 2,
    # The delay until the first retry
    "interval_start": 0.2,
    # How many seconds added to the interval for each retry
    "interval_step": 0.2,
    # Maximum number of seconds to sleep between each retry
    "interval_max": 0.6,
}
