# Putting Minerva on the web

This gives you a private web address (for example https://minerva-yourname.onrender.com) that works in any browser, protected by a password you choose. No Terminal is needed. It uses Render, which builds the app from a GitHub folder.

## 1. Put the files on GitHub (5 minutes)

1. Create a free account at github.com and press **New repository**. Name it `minerva`, set it to **Private**, and press Create.
2. On the empty repository page, choose **uploading an existing file**.
3. Unzip `minerva-v0.3.zip`, open the `minerva` folder, select everything inside it and drag it onto the GitHub page. Press **Commit changes**.

## 2. Deploy on Render (5 minutes)

1. Create an account at render.com and sign in with GitHub.
2. Press **New**, then **Blueprint**, and choose your `minerva` repository. Render reads `render.yaml` and fills in everything.
3. When asked for **MINERVA_PASSWORD**, type the password you want to sign in with. Use something long. Anyone with the address and the password can see your deals.
4. Press **Apply**. The first build takes a few minutes. When it says Live, open the address shown at the top of the service page and sign in.

The blueprint uses Render's paid Starter plan with a 1 GB disk. Check the current price on Render's pricing page. The disk is what keeps your sites, documents, mandate, API keys and Outlook connection when the service restarts.

## Free option, with a catch

On Render's free plan there is no disk, so everything you add is lost whenever the service restarts or sleeps, and it sleeps after about 15 minutes idle. That is fine for a demo, since the illustrative deals reload each time, but not for real deals. To use it: press **New**, then **Web Service**, choose the repository, set **Runtime** to Docker, add the environment variable `MINERVA_PASSWORD`, and pick the Free instance type.

## After it is live

* **Claude key.** Add it in Settings, or set `ANTHROPIC_API_KEY` in Render's Environment tab.
* **Outlook.** Works the same as on the Mac. In Inbox, paste your Azure client ID and sign in with the code shown.
* **Sign out.** Bottom left of the app.
* **Updating.** Upload new files to GitHub and Render redeploys itself.
* **Listing refreshes.** Agent websites are more likely to block a cloud server than your own computer. If a source shows Blocked, the bundled snapshot listings are shown instead.
* **Password wall.** The app refuses to start without `MINERVA_PASSWORD`. Anything you can reach without signing in is limited to a health check that returns "ok".

## Other hosts

The included `Dockerfile` works on any Docker host (Fly.io, Railway, a small VPS). Set `MINERVA_PASSWORD`, mount a persistent volume at `/data`, and expose port 8080.
