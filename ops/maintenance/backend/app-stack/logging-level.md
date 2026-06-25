# Changing Backend Log Level

Use `LOG_LEVEL` to control backend logging. Common values are `DEBUG`, `INFO`,
`WARNING`, `ERROR`, and `CRITICAL`.

The backend reads this value when the process starts, so changing the log level
for an already-running backend requires a service restart.

## Steps

1. Update the backend environment configuration:

   ```sh
   LOG_LEVEL=DEBUG
   ```

2. Restart only the backend service so the new value is loaded:

   ```sh
   docker compose up -d backend
   ```

3. Check the backend logs:

   ```sh
   docker compose logs -f backend
   ```

4. When finished debugging, restore the usual level, normally:

   ```sh
   LOG_LEVEL=INFO
   ```

5. Restart `backend` again after restoring the value.

Avoid rebuilding or restarting unrelated services unless the deployment itself
requires it.
