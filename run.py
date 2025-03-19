import asyncio
from playwright.async_api import async_playwright 
from pathlib import Path
import sys
import logging
import json
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
load_dotenv()

# Log to the stdout and to a file, with the time on each line
logger = logging.getLogger(__name__)
logging.basicConfig(filename='jobalerts.log', level=logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


async def main():
    async with async_playwright() as p:  

        logger.info("Starting playwright context")
        context = await p.chromium.launch_persistent_context("./session_data", headless=False, timeout=0)
        
        logger.info("Loading known links from known_links.txt if it exists")
        urls_to_ignore = set()
        known_links= Path('./known_links.txt')
        if known_links.is_file(): 
            with open(known_links,'r') as file:
                for line in file:
                    urls_to_ignore.add(line.strip())


        
        logger.info("Loading opened tabs from tabs.txt if it exists")
        tabs_list= Path('./tabs.txt')
        if tabs_list.is_file():  
            with open(tabs_list,'r') as file:
                for line in file:
                    page=await context.new_page()
                    await page.goto(line.strip())

        while True:
            total_new_links=0
            pages_with_issues=0
            mail_body=""

            for page in context.pages:

                logger.info("Counting links already on page, to notify user of any large drop")
                count_before_reload=len(await get_links(page))
                page_title=await page.title() 
                page_url = page.url.split('?')[0]


                logger.info("Reloading "+page_url)
                await page.reload()

                logger.info("Waiting a bit for the page to load")
                await asyncio.sleep(5)

                logger.info("Fetching all links present on "+page_url)
                links = await get_links(page)

                logger.info(f"{len(links)} links found, checking how many are new")
                new_links=[[url,text] for [url, text] in links if url not in urls_to_ignore]

                logger.info(f"{len(new_links)} new links found, marking them as known")
                with open(known_links,'a') as file:
                    for [url, text] in new_links:  
                        file.write(url+'\n')
                        urls_to_ignore.add(url)

                if len(links)<count_before_reload/2:
                    logger.info(f"{page_title} has very few links, alert needed")
                    pages_with_issues+=1
                    mail_body  += f'\n{page_title} had {count_before_reload} links before reloade and now only {len(links)}\n'
                
                elif page_url not in urls_to_ignore:
                    logger.info(f"{page_title} ({page_url}) is new, user probably just opened it, let's add it and its links to ignore list")
                    # The page we're on is new, we'll probably get many new links but there's no need to notify the user
                    
                    with open(known_links,'a') as file:
                        file.write(page_url+'\n')
                        urls_to_ignore.add(page_url)

                elif len(new_links)>0 : 
                    logger.info(f"{page_title} has {len(new_links)} new links, user will be notified")
                    list= '\n'.join(['- '+title+' : '+url for [url, title] in new_links])
                    total_new_links+=len(new_links)
                    mail_body+= f'{page_title} has {len(new_links)} new links : \n{list}\n\n'
                else :
                    logger.info(f"{page_title} has {len(links)} links but nothing new")

            if mail_body!="":
                logger.info("New links found, sending email.") 
                subject= "LinksWatcher71 : {pages_with_issues} page issue" if pages_with_issues>0 else f'LinksWatcher71 : {len(new_links)} new links found'
                send_email(subject, mail_body)
            else:
                logger.info("No new links") 

            logger.info("Saving open tabs to load then next time the script starts") 
            with open(tabs_list,'w') as file:
                file.write('\n'.join([page.url for page in context.pages if page.url != 'about:blank' ]))

            wait_seconds = 60*10
            logger.info(f"Waiting {wait_seconds} seconds before checking for change")
            await asyncio.sleep(wait_seconds)



def get_links(page):
    return page.evaluate("([]) => Array.from(document.links).map(item => [new URL(item.href, document.baseURI).href.split('?')[0],item.textContent.trim()])", [])
 

def send_email(subject, body): 
    sender = os.getenv("USER_GMAIL_ADRESS")
    recipient = os.getenv("TARGET_EMAIL")
    password = os.getenv("USER_GMAIL_APP_PASSWORD").replace(" ", "")
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = recipient
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login(sender, password)
       smtp_server.sendmail(sender, [recipient], msg.as_string())
    print("Message sent!")


asyncio.run(main())

