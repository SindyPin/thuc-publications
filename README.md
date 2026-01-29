# Auto-Update Publications from Semantic Scholar

This project automatically fetches publications from Semantic Scholar API and generates an HTML file that can be embedded in your website.

## 🚀 Quick Setup (Step-by-Step)

### Step 1: Create a GitHub Repository

1. Go to [github.com](https://github.com) and sign in
2. Click the **+** button → **New repository**
3. Name it: `thuc-publications` (or any name you prefer)
4. Set to **Public** (required for free GitHub Pages)
5. Check **"Add a README file"**
6. Click **Create repository**

### Step 2: Upload the Files

1. In your new repository, click **Add file** → **Upload files**
2. Drag and drop these files:
   - `fetch_publications.py`
   - `requirements.txt` (create this with content: `requests`)
3. Click **Commit changes**

### Step 3: Create the GitHub Actions Workflow

1. In your repository, click **Add file** → **Create new file**
2. Name it: `.github/workflows/update-publications.yml`
3. Copy the content from the workflow file provided
4. Click **Commit changes**

### Step 4: Find Your Semantic Scholar Author ID

1. Go to [semanticscholar.org](https://www.semanticscholar.org/)
2. Search for "Thuc Duy Le"
3. Click on the correct author profile
4. The URL will be like: `https://www.semanticscholar.org/author/Thuc-Duy-Le/2482441`
5. The number at the end (`2482441`) is the Author ID

### Step 5: Update the Author ID in the Script

1. Open `fetch_publications.py` in your repository
2. Click the pencil icon to edit
3. Find this line:
   ```python
   AUTHOR_ID = "2482441"
   ```
4. Replace with the correct ID if different
5. Click **Commit changes**

### Step 6: Run the Workflow Manually (First Time)

1. Go to the **Actions** tab in your repository
2. Click on **Update Publications** workflow
3. Click **Run workflow** → **Run workflow**
4. Wait for it to complete (green checkmark)

### Step 7: Check the Results

1. Go back to your repository's main page
2. You should see new files:
   - `publications.json` - Raw data
   - `publications.html` - HTML to embed in your website

### Step 8: Embed in Your Website

**Option A: Direct iframe (Easiest)**
```html
<iframe 
  src="https://raw.githubusercontent.com/YOUR_USERNAME/thuc-publications/main/publications.html" 
  width="100%" 
  height="800px" 
  frameborder="0">
</iframe>
```

**Option B: JavaScript fetch (Better control)**
```html
<div id="publications-container"></div>
<script>
fetch('https://raw.githubusercontent.com/YOUR_USERNAME/thuc-publications/main/publications.html')
  .then(response => response.text())
  .then(html => {
    document.getElementById('publications-container').innerHTML = html;
  });
</script>
```

**Option C: Manual copy (Full control)**
1. Download `publications.html` from GitHub
2. Copy the content into your `index.html` in the Publications section

---

## 📅 Automatic Updates

The workflow runs automatically every Sunday at midnight UTC. You can also:
- Trigger manually from the Actions tab
- Change the schedule by editing the cron expression in the workflow file

### Cron Examples:
```yaml
# Every Sunday at midnight
- cron: '0 0 * * 0'

# Every day at 6 AM UTC
- cron: '0 6 * * *'

# Every Monday and Thursday at noon
- cron: '0 12 * * 1,4'
```

---

## 🔧 Troubleshooting

### "Author not found" error
- Verify the Author ID at semanticscholar.org
- Try the author search function in the script

### Workflow not running
- Check the Actions tab for error messages
- Ensure the repository has Actions enabled (Settings → Actions)

### Publications missing
- Semantic Scholar may not have all papers indexed
- Consider using multiple sources (see Advanced section)

---

## 📚 Files Overview

| File | Purpose |
|------|---------|
| `fetch_publications.py` | Main script that fetches and formats publications |
| `.github/workflows/update-publications.yml` | GitHub Actions workflow for automation |
| `publications.json` | Raw publication data (auto-generated) |
| `publications.html` | HTML output for embedding (auto-generated) |

---

## 🔄 Alternative: Using Google Scholar with `scholarly`

If Semantic Scholar is missing papers, you can use the `scholarly` library:

```python
# Install: pip install scholarly

from scholarly import scholarly

author = scholarly.search_author_id('wMSCRxUAAAAJ')  # Dr. Thuc Le's Google Scholar ID
scholarly.fill(author, sections=['publications'])

for pub in author['publications']:
    print(pub['bib']['title'])
```

**Note:** Google Scholar may rate-limit or block automated requests. Use with caution and add delays between requests.

---

## 📝 License

MIT License - Feel free to use and modify!
