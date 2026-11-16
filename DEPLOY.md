# Put JW Opportunity Desk live

The design: GitHub reads the portals four times a working day and saves the data. Cloudflare Pages publishes the site from GitHub, so each scan goes live within a minute or two. Both are free at this size. The only paid item is AI, billed per use on your Anthropic key.

You need about 30 minutes, a GitHub account and a Cloudflare account. No software to install.

## Part A. Put the code on GitHub (10 minutes)

1. Unzip `jw-opportunity-desk.zip` on your computer.
2. On github.com, click **New repository**. Name it `jw-opportunity-desk`, choose **Private**, and click **Create repository**.
3. On the empty repository page, click **uploading an existing file**.
4. Open the unzipped folder, select everything inside it (including the `.github` folder), and drag it onto the page. Wait until every file is listed, then click **Commit changes**.

## Part B. Switch on the scanner (5 minutes)

5. In the repository, open **Settings > Actions > General**. Under **Workflow permissions**, choose **Read and write permissions** and click **Save**.
6. Open the **Actions** tab. If GitHub asks, click **I understand my workflows, go ahead and enable them**.
7. Click **scan** on the left, then **Run workflow > Run workflow**. A run takes about five minutes.
8. Open the run and then **Read sources**. Each portal shows `OK` or `FAILED`. If one fails, copy the `FAILED` lines and send them to me. A failed source keeps its previous data, so the site never goes empty.

8a. For the AI reader on the scheduled scan, open **Settings > Secrets and variables > Actions > New repository secret**, name it `ANTHROPIC_API_KEY` and paste the same key you use in Part C. Without it, the scan runs on the rules reader alone.

From now on the scan runs by itself at 09:00, 12:00, 15:00 and 18:00 Pakistan time, every day.

## Part C. Publish the site on Cloudflare Pages (10 minutes)

9. Sign in at dash.cloudflare.com. Open **Workers & Pages > Create > Pages > Connect to Git** and pick `jw-opportunity-desk`.
10. Set **Framework preset** to `None`, leave **Build command** empty, and set **Build output directory** to `app`. Click **Save and Deploy**.
11. Open the project's **Settings > Variables and Secrets** and add these as **Secret**:
    - `SITE_PASSPHRASE`: the passphrase colleagues type to open the site.
    - `ANTHROPIC_API_KEY`: a new key from console.anthropic.com. Set a monthly spend limit there.
12. Create the team store. Go to **Storage & Databases > KV > Create**, name it `jwod-store`, then return to the Pages project and open **Settings > Bindings > Add > KV namespace**. Set **Variable name** to `STORE` and pick `jwod-store`.
13. Open **Deployments** and click **Retry deployment** on the latest one, so the settings apply. Open the `.pages.dev` link and enter the passphrase.

Without the key, the site works with no AI buttons. Without the KV store, it works with no team pipeline.

## Part D. Daily Teams post (optional, 5 minutes)

14. In the Teams channel, open **... > Workflows > Post to a channel when a webhook request is received**, finish the steps and copy the URL it gives you.
15. In GitHub, open **Settings > Secrets and variables > Actions**. On **Secrets**, add `TEAMS_WEBHOOK_URL` with that URL. On **Variables**, add `SITE_URL` with your `.pages.dev` link.

Each scan then posts the relevant tenders first seen in that scan.

## What it costs

| Item | Free allowance | Our use |
| --- | --- | --- |
| GitHub Actions, private repository | 2,000 minutes a month | About 500 to 700 minutes |
| Cloudflare Pages | 500 deployments a month | About 100 |
| Cloudflare Functions and KV | 100,000 requests and 1,000 writes a day | Well under |
| Anthropic API | Pay per use | Set a spend limit |

## Things to know

- **A portal may refuse GitHub's servers.** GitHub runs in US data centres, and Pakistani government sites sometimes block foreign traffic. If a source keeps failing, the scan can run on a Jazz machine as a self-hosted GitHub runner instead, with no code change.
- **The passphrase is MVP-grade security.** For production, put the site behind Jazz single sign-on (Cloudflare Access or Jazz hosting) and get IT approval for tender text going to the Anthropic API.
- **To change a rule**, edit `build/rules.py` on GitHub. The next scan applies it.
