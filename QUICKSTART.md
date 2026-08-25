# Quick Start Guide 🚀

Welcome! This guide will help you understand and work with this repository.

## 📁 Repository Structure

```
nikhilpravinpise/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   ├── workflows/
│   │   ├── update-profile-art.yml  # Daily wordmark + heatmap regeneration
│   │   └── greetings.yml           # Welcome first-time contributors
│   ├── FUNDING.yml
│   └── PULL_REQUEST_TEMPLATE.md
├── scripts/
│   ├── fetch_contributions.py      # Scrape contribution calendar -> JSON
│   ├── render_heatmap_svg.py       # JSON -> animated heatmap SVG
│   ├── make_wordmark_svg.py        # Text -> animated 3D ASCII wordmark SVG
│   ├── requirements.txt            # Pinned dependencies
│   └── fonts/                      # Archivo Black (SIL OFL 1.1)
├── data/
│   └── contributions.json          # Raw daily counts + derived stats
├── wordmark.svg                    # Generated hero art
├── contrib-heatmap.svg             # Generated contribution graph
├── README.md                       # Main profile README
├── LICENSE                         # MIT License
├── SECURITY.md                     # Security policy
├── CONTRIBUTING.md                 # Contribution guidelines
├── CODE_OF_CONDUCT.md              # Community standards
├── CHANGELOG.md                    # Version history
├── .gitignore                      # Git ignore rules
└── QUICKSTART.md                   # This file!
```

## 🎯 What This Repository Contains

### 1️⃣ **GitHub Profile README**
- The `README.md` renders on your profile: `github.com/nikhilpravinpise`
- Terminal-styled hero with an animated 3D ASCII wordmark and a live contribution heatmap built from real data

### 2️⃣ **Automated Art Pipeline**
- `update-profile-art.yml` runs daily (~05:20 UTC) and on pushes that touch the scripts
- Fetches real contribution data, re-renders both SVGs, and auto-commits any refreshes

## 🚀 Getting Started

### For Viewing

1. **Visit your GitHub profile**: `https://github.com/nikhilpravinpise`
2. **See the README** with the animated wordmark and heatmap (auto-refreshed daily)
3. **Try the interactive terminal site** - linked in the README badges

### For Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/nikhilpravinpise/nikhilpravinpise.git
   cd nikhilpravinpise
   ```

2. **Install dependencies**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r scripts/requirements.txt
   ```

3. **Regenerate the art locally**
   ```bash
   python scripts/make_wordmark_svg.py --out wordmark.svg
   python scripts/fetch_contributions.py
   python scripts/render_heatmap_svg.py
   ```

   Note: exact byte-for-byte SVG output depends on platform font rasterization;
   CI is the source of truth for the committed art.

4. **Commit and push**
   ```bash
   git add .
   git commit -m "your message"
   git push origin main
   ```

## 📝 Common Tasks

### Change the Wordmark Text
Set the `WORDMARK_TEXT` environment variable (defaults to `NIKHIL`) and re-run `make_wordmark_svg.py`.

### Tune Heatmap Colors or Buckets
Edit `PALETTE` or `level_for()` in `scripts/render_heatmap_svg.py`, re-render, and review visually.

## 🔧 Troubleshooting

### Heatmap Shows No Data
- Run `fetch_contributions.py` manually and check stderr - GitHub's calendar markup may have changed
- Confirm `data/contributions.json` was updated

### Workflow Failing
- Check Actions tab for error logs
- Verify GITHUB_TOKEN permissions (`contents: write` is required)
- Ensure YAML syntax is correct

## 💡 Tips

- **Keep README updated** - It's your digital business card!
- **Commit generated art together with data changes** - The workflow does this automatically
- **Lint before pushing** - `ruff check scripts` keeps the Python clean

## 🆘 Need Help?

- 📖 Read [CONTRIBUTING.md](./CONTRIBUTING.md)
- 🐛 Open an issue for bugs
- 💡 Open feature request for suggestions
- 📧 Email: nikhilpise2006@gmail.com
- 💼 LinkedIn: [Nikhil Pise](https://linkedin.com/in/nikhil-pravin-pise)

## 🎉 You're All Set!

Happy coding! 🚀
