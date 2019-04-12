Description
***********

**OAuth-Sidecar**, as its name says, is a "sidecar" container which works like a normal Docker container, but behaves differently during the startup and termination phases.

This container acts as a reverse **HTTP proxy** for another container and it authenticates the user through the configured OAuth 2 service (currently only Google OAuth is available).

If the user is not authenticated the container redirects to the OAuth2 login page.

