# Operations & Deployment

StockFlow relies on GitHub Actions for CI/CD and K3s for runtime orchestration.

## CI/CD Pipeline

The CI/CD pipeline is handled by two main workflows in `.github/workflows/`:

- **Build & Test (`build.yml`)**: Triggers on `push` to any branch or via `workflow_dispatch`. It performs the following:
  1. Extracts the `appVersion` from `helm/Chart.yaml`.
  2. Builds Docker images for all services. **Note**: The build order in the workflow currently lists `signal-engine`, `stockflow-controller`, `market-intel-engine`, and then `stockflow-common` (built twice).
  3. Publishes images to **Docker Hub** (not GHCR).
  4. Triggers the deployment workflow.

  The workflow accepts `namespace` and `image-version` as inputs (via `workflow_dispatch`). By default, both are set to `"dev"`.
- **Deploy (`deploy-stockflow.yml`)**: A reusable workflow called by `build.yml`. It connects to the self-hosted runner, sets up the environment, and executes `helm/deploy_helm.sh` to update the cluster.

## Deployment Setup

1. **Secrets**: Ensure the following are defined as GitHub Secrets and/or Kubernetes secrets:
   - `OPENAI_API_KEY`: Key for GPT-5 analysis.
   - `SF_API_KEY`: A secure key token string used for internal StockFlow API authentication.
   - `SMTP_PASSWORD`: Password for the alert email account.
2. **Infrastructure**: Run `./infra/install-helm.sh` to ensure Helm is available.
3. **Manual Deploy**: Run `./helm/deploy_helm.sh <OPENAI_API_KEY> <SMTP_PASSWORD> <SF_API_KEY> [namespace] [version]`.
   - If not provided, `namespace` and `version` both default to `"dev"`.

---

## Internal API Reference

All administrative requests to the Controller must include `X-API-Key` in the headers.

### StockFlow Controller (:9000)

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/admin/health` | `GET` | Basic health check. |
| `/api/admin/maintenance/status` | `GET` | Returns current maintenance mode status. |
| `/api/admin/maintenance/{status}`| `GET` | Sets maintenance mode (`on`/`off`). Triggers rollout restart of Signal Engine. |
| `/api/admin/trigger-cron` | `GET` | Manually triggers the `signal-check-cronjob`. |
| `/api/admin/top-stocks` | `POST` | Updates the list of tickers in the `top-stocks-cm` ConfigMap. |

### Signal Engine (:8000)

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/api/health` | `GET` | Health check (returns maintenance status if enabled). |
| `/api/{stock_id}` | `GET` | Calculates the final BharatQuant signal for a given stock. |
| `/api/{stock_id}/{option}` | `GET` | Calculates an individual indicator (e.g., `rsi`, `macd`) for a stock. |

### Market Intel Engine (:8000)

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health` | `GET` | Health check. |
| `/chat` | `POST` | Sends a prompt to the GPT-5 model (returns JSON). |
