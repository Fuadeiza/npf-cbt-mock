# Deploying the NPF CBT Mock Exam — a learning guide

This guide teaches deployment, not just recipes. It goes:

1. **Understand the app's shape** (what constrains the deploy)
2. **Run it in Docker locally** (the transferable skill)
3. **Deploy to a VPS** with HTTPS (the "real" deployment)
4. **The 5-minute shortcut** (Render) once you understand the above

---

## 0. The one constraint that shapes everything

This app stores exam attempts **in memory**, and one process serves both the
API and the frontend. Consequences:

- **Run exactly one instance / one worker.** Two workers = two separate
  memory stores; an exam started on one couldn't be submitted on the other.
  (This is why the Dockerfile runs a single `uvicorn` process, not `gunicorn`
  with many workers.)
- **Restarts wipe in-progress attempts.** Fine for a practice app — a candidate
  just starts again. If you later want to keep results, swap
  `InMemoryAttemptRepository` for a database-backed one (the port/interface is
  already there in `backend/app/application/ports.py`).
- **No database to provision.** One less thing to deploy.

Keep this in mind: every platform below is configured for a *single* instance.

---

## 1. What a container is (and why it's the real skill)

A **Docker image** is your app + Python + its dependencies frozen into one
portable artifact. A **container** is a running copy of that image. The point:
the image runs *identically* on your laptop, a VPS, or any cloud — so you learn
this once and deploy anywhere.

The [`Dockerfile`](Dockerfile) here does four things (read it — it's commented):
install deps, copy the backend + frontend, then run one uvicorn process.

## 2. Run it in Docker locally

Install [Docker Desktop](https://www.docker.com/products/docker-desktop/), then:

```bash
# from the project root
docker build -t npf-cbt .          # build the image (named "npf-cbt")
docker run --rm -p 8080:8000 npf-cbt   # run it, mapping localhost:8080 -> container:8000
```

Open http://localhost:8080. `Ctrl+C` stops it.

What you just learned: `-p host:container` maps ports; `--rm` deletes the
container when it stops; the image is reusable and shippable.

---

## 3. Deploy to a VPS (the learning path)

You'll rent a tiny Linux server, install Docker on it, and run the same image
behind **Caddy** (a web server that gives you automatic HTTPS). This teaches
SSH, Linux, containers, reverse proxies, DNS, and TLS — the whole stack.

### 3a. Get a server

Create the cheapest **Ubuntu 24.04** droplet/VM on any of:
DigitalOcean, Hetzner, Vultr, Linode (~$4–6/month, 1 vCPU / 1 GB is plenty).
You'll get a public **IP address** and a root password or SSH key.

### 3b. Point a domain at it (needed for HTTPS)

In your domain registrar's DNS settings, add an **A record**:

```
exam.yourdomain.com  ->  <your server's IP>
```

No domain yet? You can still test over plain HTTP by IP (skip Caddy — see 3f).
But HTTPS needs a domain, so grab a cheap one (Namecheap, Porkbun, ~$1–10/yr).

### 3c. Log in and install Docker

```bash
ssh root@<your-server-ip>

# install Docker Engine + compose plugin (official convenience script)
curl -fsSL https://get.docker.com | sh
```

### 3d. Get your code onto the server

Easiest is Git. Push this project to GitHub, then on the server:

```bash
git clone https://github.com/<you>/<repo>.git
cd <repo>
```

(No GitHub? `scp -r ./npf-cpt-mock root@<ip>:/root/` from your laptop instead.)

### 3e. Set your domain and launch

Edit [`Caddyfile`](Caddyfile) and replace `exam.example.com` with your real
subdomain (e.g. `exam.yourdomain.com`). Then:

```bash
docker compose up -d --build
```

That's it. Caddy detects the domain, fetches a Let's Encrypt certificate, and
serves your app at **https://exam.yourdomain.com**. Give DNS a few minutes to
propagate first.

Useful commands to learn:

```bash
docker compose ps          # what's running
docker compose logs -f app # tail the app's logs
docker compose down        # stop everything
docker compose up -d --build   # redeploy after a code change (git pull first)
```

### 3f. No domain? Plain HTTP by IP

Skip compose/Caddy and just run the app container directly:

```bash
docker build -t npf-cbt .
docker run -d --restart unless-stopped -p 80:8000 --name npf npf-cbt
```

Visit `http://<your-server-ip>`. No HTTPS, but great for a first taste.
(Open port 80 in the provider's firewall if you can't reach it.)

---

## 4. The 5-minute shortcut: Render

Once you understand the above, shipping is trivial. This repo ships a
[`render.yaml`](render.yaml) **blueprint**, so Render provisions everything for
you — no clicking through forms:

1. Push this repo to GitHub (next section).
2. On [render.com](https://render.com): **New → Blueprint** → connect the repo.
3. Render reads `render.yaml`, builds the `Dockerfile`, and creates the service
   pinned to **1 instance** (the in-memory constraint) on the free plan.
4. Deploy. You get a `https://…onrender.com` URL with TLS already handled.
   Every future `git push` auto-redeploys.

The container listens on Render's `$PORT` automatically (see the `Dockerfile`
`CMD`), so there's nothing else to configure.

> Free-tier note: Render spins the service down after ~15 min idle, so the
> first request after a nap takes ~30–50s to wake. Fine for practice; upgrade
> to a paid instance if you want it always-on.

---

## Which should *you* pick?

- **To learn:** do §2 (Docker locally) then §3 (VPS). You'll understand what
  every managed platform is doing for you.
- **To just ship fast:** §4 (Render), 5 minutes, free.
- **Both** use the exact same `Dockerfile` — that's the payoff of learning
  containers first.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Browser can't reach the site | Firewall blocks 80/443 | Open those ports in your VPS provider's firewall |
| HTTPS fails / cert error | DNS not propagated, or wrong domain in `Caddyfile` | Wait, verify the A record, check `docker compose logs caddy` |
| Exam "session not found" on submit | App restarted, or >1 instance | Run a single instance; don't restart mid-exam |
| Port 8080 already in use locally | Something else is on it | Use another host port, e.g. `-p 9000:8000` |
