# Azure VM Deployment Guide

This guide describes the intended production pipeline. It does not provision
resources automatically. Complete owner-only Azure, DNS, GitHub and Google setup
before enabling deployment.

## Deployment Contract

After the initial setup, a push to `main` runs [Checks](../.github/workflows/checks.yml).
If every test and container smoke check succeeds, [Deploy production](../.github/workflows/deploy.yml):

1. authenticates to Azure through GitHub OIDC without a client secret;
2. builds and pushes an immutable `sha-<commit>` image to Azure Container Registry;
3. invokes the root-owned deployment script on the existing VM;
4. retrieves the production environment from Key Vault using the VM managed identity;
5. runs migrations, starts the new container and checks liveness/readiness;
6. restores the previous container if the new release fails health checks;
7. verifies the release through the public HTTPS domain; and
8. creates a CalVer-style GitHub release such as `release-20260926.42`.

`AZURE_DEPLOYMENT_ENABLED` must be the repository variable `true` before this
workflow deploys anything. Leave it unset while preparing or testing resources.
The first commit that adds a `workflow_run` deployment may not deploy because the
workflow was not present on the default branch when its Checks run began; the next
successful push will trigger it.

Database migrations run before the web container changes. Container rollback
does not reverse a migration. Keep migrations backward compatible with the
currently running release and use multi-step expand/migrate/contract changes for
destructive schema work.

## Manual Private Pilot

The private pilot is a smaller deployment path than the automated production
contract. It builds the image directly on the VM, uses SQLite and host media on
the managed data disk, and limits application sign-in to Google OAuth test users.
It does not require ACR, Key Vault, GitHub OIDC or the deployment workflow.

Use [compose.pilot.yml](../deploy/compose.pilot.yml) with a root-owned environment
file based on [pilot.env.example](../deploy/pilot.env.example). Create the host
database and media directories as UID/GID `10001` before starting the container.
The pilot Caddy example blocks public access to administration and operational
health endpoints; run those checks through the VM loopback interface instead.

SQLite is a pilot constraint, not the intended wider-launch database. Back up
the database and media together, test restoration, and move to PostgreSQL before
traffic or concurrency grows. A managed disk is not itself a backup.

## Values to Choose

These identifiers are safe to share when asking for command guidance:

- Azure subscription ID and tenant ID;
- resource group, VM, registry and Key Vault names;
- GitHub organisation/repository name;
- production domain: `bpmimage.com`;
- managed-disk mount path; and
- Google OAuth client ID.

Never send or commit access tokens, SSH private keys, API keys, database
passwords, Django secret keys, OAuth client secrets or the Key Vault environment
secret value.

## One-Time Azure Setup

The Azure account owner must:

1. Reserve a static public IP for the existing VM.
2. Attach and mount a separate managed data disk for production media, for
   example at `/srv/bpm-memory-maker/production`. Add a stable `/etc/fstab`
   entry and test a reboot. A disk is not a backup; configure snapshots/backups
   separately and decide how expired photos leave those backups.
3. Enable the VM system-assigned managed identity.
4. Create an Azure Container Registry and grant the VM identity `AcrPull` scoped
   only to that registry.
5. Create a Key Vault using Azure RBAC and grant the VM identity
   `Key Vault Secrets User` scoped to that vault.
6. Create a Microsoft Entra application/service principal for GitHub Actions,
   add a federated credential for the GitHub `production` environment (subject
   `repo:OWNER/REPOSITORY:environment:production`), then restrict that
   environment's deployment branches to `main`,
   and grant it:
   - `AcrPush` on the registry; and
   - a narrow custom role permitting VM Run Command on this VM. Avoid broad
     subscription-level `Contributor` access.
7. Allow public inbound TCP `80` and `443` in the VM NSG. Restrict SSH `22` to
   trusted source IPs or use Azure Bastion/JIT. Do not expose `8000`, database
   ports, development servers or future worker interfaces.
8. Ensure the VM can reach ACR, Key Vault, the database, GitHub release checks,
   certificate authorities and configured AI endpoints over HTTPS.

Official references:

- [GitHub OIDC with Azure](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-azure)
- [Connect GitHub Actions to Azure](https://learn.microsoft.com/azure/developer/github/connect-from-azure)
- [Azure Login action](https://github.com/Azure/login)
- [ACR authentication](https://learn.microsoft.com/azure/container-registry/container-registry-authentication)
- [ACR roles](https://learn.microsoft.com/azure/container-registry/container-registry-rbac-built-in-roles-overview)
- [Azure VM Run Command](https://learn.microsoft.com/azure/virtual-machines/run-command-overview)
- [Managed identities](https://learn.microsoft.com/entra/identity/managed-identities-azure-resources/overview)
- [Key Vault RBAC](https://learn.microsoft.com/azure/key-vault/general/rbac-guide)
- [Network security groups](https://learn.microsoft.com/azure/virtual-network/network-security-groups-overview)

## One-Time VM Setup

Install Docker Engine with Compose plugin **2.30.0 or newer**, Azure CLI and Caddy
from their official repositories. Pin and maintain supported versions. Then install the
repository-owned files:

```sh
sudo install -d -m 0755 /opt/bpm-memory-maker
sudo install -d -m 0750 /etc/bpm-memory-maker
sudo install -m 0755 deploy/bpm-deploy /usr/local/sbin/bpm-deploy
sudo install -m 0644 deploy/compose.production.yml /opt/bpm-memory-maker/compose.production.yml
sudo install -m 0600 deploy/deploy.conf.example /etc/bpm-memory-maker/deploy.conf
```

Edit `/etc/bpm-memory-maker/deploy.conf` as root with the non-secret resource
names and persistent media path. Replace the example Caddy domain, install it as
the system Caddy configuration and validate it before reloading Caddy.
The workflow refreshes `bpm-deploy` and the Compose file from the exact checked
commit on every deployment; the initial manual copies bootstrap that process.

Production and development share the VM but must not share runtime state:

| Concern | Production | Development |
| --- | --- | --- |
| Linux ownership | root-managed config and UID/GID `10001` media | developer account |
| Network | Caddy on public `80/443`; app on `127.0.0.1:8000` | bind to another loopback port, accessed by SSH forwarding |
| Database | production database and credentials | SQLite or separate development database |
| Files | dedicated production media path/disk | repository-local ignored `media/` |
| Secrets | Key Vault production secret | ignored local environment file |
| Containers | production Compose project | separate project/name/network, if used |

Do not mount production media into development containers or use production
credentials during local testing.

## Production Environment Secret

Create a multiline Key Vault secret using
[production.env.example](../deploy/production.env.example) as the key list.
The value is written to a root-only file under `/run` for Docker Compose and is
removed on reboot. It must include a random Django key, the public domain and
CSRF origin, a TLS-enabled database URL and `127.0.0.1` in allowed hosts for the
container health check.

Do not put this secret in GitHub. The deployment workflow receives no runtime
application credentials.

## GitHub Configuration

Create a protected `production` environment and configure these repository or
environment variables:

```text
AZURE_CLIENT_ID
AZURE_TENANT_ID
AZURE_SUBSCRIPTION_ID
AZURE_ACR_NAME
AZURE_RESOURCE_GROUP
AZURE_VM_NAME
APP_DOMAIN
AZURE_DEPLOYMENT_ENABLED
```

All are identifiers or a feature flag, not application secrets. Protect `main`,
require the Checks workflow, block direct pushes and consider required review for
the production environment until rollback and restoration have been exercised.

## DNS and HTTPS

Point an `A` record for the chosen hostname to the VM static public IP. Ensure
it resolves publicly before starting Caddy. Caddy obtains and renews certificates
automatically when ports `80/443` are reachable and the hostname resolves to the
VM. Replace the placeholder in [Caddyfile.example](../deploy/Caddyfile.example).

The current image serves static assets through WhiteNoise. Customer media must
never be exposed as a public static directory; future media downloads will pass
through ownership checks or an internal Nginx/Caddy handoff.

## Google Login

In [Google Auth Platform](https://console.cloud.google.com/auth/overview):

1. Create/select a project and configure branding, support email and authorised
   domain. For a public external app, provide working home, privacy-policy and
   terms URLs before publishing.
2. Choose an external audience and add your Google account as a test user while
   the app is in testing mode.
3. Request only OpenID Connect identity scopes (`openid`, `email`, `profile`).
4. Create an OAuth client of type **Web application**.
5. Add the exact production origin and callback:

```text
https://bpmimage.com
https://bpmimage.com/accounts/google/login/callback/
```

6. For forwarded local development, add the exact origin/callback you use:

```text
http://localhost:8001
http://localhost:8001/accounts/google/login/callback/
```

7. Store the client ID and secret in the Key Vault environment secret. The
   client ID may be shared for troubleshooting; the client secret must not.
8. Test with an allowed test user. Publish the app when the policies and public
   domain are ready. Additional sensitive scopes may require Google verification;
   the basic identity scopes normally avoid that additional scope review.

Redirect URI scheme, host, port, path and trailing slash must match exactly.
Do not create duplicate provider credentials in Django admin and settings.

Official references:

- [Google OAuth web-server applications](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Google OAuth consent and verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/policy-compliance)
- [django-allauth Google provider](https://docs.allauth.org/en/latest/socialaccount/providers/google.html)

## Activation and Verification

Before setting `AZURE_DEPLOYMENT_ENABLED=true`:

1. Verify the VM can use its identity to read only the intended Key Vault secret
   and pull from the intended registry.
2. Run `bpm-deploy` manually with a test image and confirm rollback after an
   intentionally failing health check.
3. Confirm database restore and media-disk recovery procedures.
4. Confirm Caddy HTTPS, `/health/`, `/ready/`, static assets and Google sign-in.
5. Confirm development is reachable only through SSH forwarding.
6. Merge a harmless change and watch Checks, deployment, public verification and
   GitHub release creation end to end.

Keep `AZURE_DEPLOYMENT_ENABLED` unset to stop automatic deployments without
deleting the workflow.