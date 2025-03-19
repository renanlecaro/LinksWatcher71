# Job alerts

This python script opens a few browser tabs with [playwright](https://playwright.dev/python/docs/library), refreshes them regularily, and alerts you if there's a new link on any of them. 
 
# Usage

Install the required packages

	pip install -r requirements.txt

Install the chromium browser 

	playwright install chromium

Create an app password for your gmail account here : https://myaccount.google.com/apppasswords

Create a file named ".env" next to the run.py file, and set its content with your gmail adress and an app password

	USER_GMAIL_ADRESS=my-email-adress@gmail.com
	USER_GMAIL_APP_PASSWORD="aaaa bbbb cccc dddd"

For the password, spaces are removed by the script, they don't matter. 

Start the script

	python run.py

A chrome window will open. 

Navigate to the sites you want to monitor. 

The script will reload the page every 10 minutes, and notify you by email if there are new links, or if the page lost half of its links (with a captcha for example). 


# Limitations

- playwright is detected by cloudflare (used by indeed) and will not work on cloudflare backed site. 
- using [playwright stealth](https://pypi.org/project/playwright-stealth/) just broke all pages, but that could be one workaround
- it would be best to implement this as a browser extension

