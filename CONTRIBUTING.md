## GitHub App checklist
1. Create an App, enable pull request + issue events, set webhook to `https://<your-domain>/webhook`.
2. Use the same secret value for the App and `GITHUB_WEBHOOK_SECRET`.
3. Install the App, capture the installation ID, and place the private key where `GITHUB_PRIVATE_KEY_PATH` points.

## Database
This essentially tracks user entities for the frontend.
Future versions of the app might switch to storing commit diffs for contextual retrievals.
