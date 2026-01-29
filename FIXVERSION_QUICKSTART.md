# Quick Start: Creating fixVersions in Jira

This guide will walk you through creating fixVersions in 5 minutes.

## Step 1: Edit Your Dates

Open `create_fix_versions.py` and find this section (around line 48):

```python
sprint_dates = [
    '2026-02-05',
    '2026-02-12',
    '2026-02-19',
    '2026-02-26',
    '2026-03-05',
    '2026-03-12'
]
```

**Replace with your own dates:**

```python
sprint_dates = [
    '2026-03-01',  # Your first release
    '2026-03-15',  # Your second release
    '2026-03-29',  # Your third release
]
```

## Step 2: Choose Your Format

Find this line (around line 58):

```python
name_format='Sprint {month_short} {day}',
```

**Replace with your preferred format:**

| Format | Example Output |
|--------|---------------|
| `'Sprint {month_short} {day}'` | Sprint Mar 01 |
| `'v{year}.{month}.{day}'` | v2026.03.01 |
| `'Release {date}'` | Release 2026-03-01 |
| `'{month_name} {day} Sprint'` | March 01 Sprint |

## Step 3: Check Your Project Key

Make sure `config.yaml` has your Jira project key:

```yaml
jira:
  base_url: https://your-company.atlassian.net/
  project_keys:
    - KAN  # ← Your project key here
```

## Step 4: Run It!

```bash
python create_fix_versions.py
```

**What happens:**
1. Browser opens to your Jira site
2. If not logged in, you'll login manually (once)
3. Script creates all versions automatically
4. Shows summary of created/skipped/failed versions
5. Browser stays open for 10 seconds so you can verify

## Step 5: Verify

Check your Jira project versions page:
```
https://your-company.atlassian.net/plugins/servlet/project-config/YOUR_PROJECT/versions
```

You should see all your new fixVersions!

## 🎯 Common Use Cases

### Weekly Sprints (Every Thursday)

```python
sprint_dates = [
    '2026-03-05',  # Week 1
    '2026-03-12',  # Week 2
    '2026-03-19',  # Week 3
    '2026-03-26',  # Week 4
]
name_format = 'Sprint Week {day}'
```

### Bi-Weekly Sprints

```python
sprint_dates = [
    '2026-03-05',
    '2026-03-19',
    '2026-04-02',
    '2026-04-16',
]
name_format = 'Sprint {month_short} {day}'
```

### Monthly Releases

```python
release_dates = [
    '2026-03-01',
    '2026-04-01',
    '2026-05-01',
    '2026-06-01',
]
name_format = 'v{year}.{month}'
```

### Semantic Versioning

```python
version_dates = [
    '2026-03-15',  # v2026.03.15
    '2026-06-15',  # v2026.06.15
    '2026-09-15',  # v2026.09.15
]
name_format = 'v{year}.{month}.{day}'
```

## ⚠️ Important Notes

1. **Date format must be YYYY-MM-DD** (with leading zeros)
   - ✅ Good: `'2026-03-05'`
   - ❌ Bad: `'2026-3-5'`

2. **Login persists** - You only login once, then the browser remembers

3. **Duplicate versions are skipped** - Safe to run multiple times

4. **Description optional** - Leave empty or add custom template:
   ```python
   description_template='Sprint ending on {date}'
   ```

## 🐛 Troubleshooting

### "Not logged in to Jira"
→ Just login manually when the browser opens. Script will detect it.

### "No project key found"
→ Add your project key to `config.yaml` under `jira.project_keys`

### "Could not find Create Version button"
→ Make sure you have admin/project lead permissions in Jira

### Versions not showing up
→ Refresh the versions page. They might already be there!

## 📝 Next Steps

Once you're comfortable with the basics:
- Check out `fixversion_examples.py` for advanced date generation
- Read `FIXVERSION_CREATOR_README.md` for full API documentation
- Customize description templates for your team's needs

---

**Need help?** Open an issue or check the full documentation in `FIXVERSION_CREATOR_README.md`
