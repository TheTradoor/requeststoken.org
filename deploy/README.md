# Deploy (mercury / Dokploy)

Dokploy project `requeststoken.org` → compose `requeststoken-org-web` (composeId `Ez8N39E_NDdLs_VuH3uKI`, sourceType raw).
Domain `requeststoken.org` → service `web`, port 5042, Let's Encrypt.

The image is built on the server from a git commit (no registry):

    git archive --format=tar <commit> | ssh root@mercury.kennethreitz.org \
      'rm -rf /tmp/rtbuild && mkdir /tmp/rtbuild && tar -x -C /tmp/rtbuild && docker build -t requeststoken-org:<commit> /tmp/rtbuild'

Then update the image tag in the compose file (Dokploy UI or `compose.update`) and redeploy (`compose.deploy`).
