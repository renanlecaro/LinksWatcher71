# Job alerts

This python script opens a few browser tabs with [playwright](https://playwright.dev/python/docs/library), refreshes them regularily, and alerts you if there's a new link on any of them. 
 
# usage

Install requirements (just playwright)

	pip install -r requirements.txt

Then start the script

	python run.py

# Limitations

- playwright is detected by cloudflare (used by indeed) and will not work on cloudflare backed site. 
- using [playwright stealth](https://pypi.org/project/playwright-stealth/) just broke all pages, but that could be one workaround
- it would be best to implement this as a browser extension

# Todo

- save each tab url and link count to a file, and reload that list when starting up
- send email when there's a new tab or issue. 
- alert if 50% fewer links than last reload
