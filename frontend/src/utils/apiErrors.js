const RATE_LIMIT_FALLBACK =
  'Too many requests. Please wait a minute and try again.';

/** Extract a user-facing message from an axios error response. */
export function getApiErrorMessage(err, fallback) {
  const status = err.response?.status;
  const detail = err.response?.data?.detail;

  if (typeof detail === 'string') {
    return detail;
  }
  if (status === 429) {
    return RATE_LIMIT_FALLBACK;
  }
  return fallback;
}
