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



logger = logging.getLogger(__name__)


handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

async def main():
    async with async_playwright() as p: 
        logger.info("Starting playwright context")
        # restart the same browser session every time
        context = await p.chromium.launch_persistent_context("./session_data", headless=False, timeout=0)
        
        urls_to_ignore = set()
        ignore_list= Path('./ignore_list.txt')
        if ignore_list.is_file(): 
            logger.info("Loading ignore_list from ignore_list.txt")
            with open(ignore_list,'r') as file:
                for line in file:
                    urls_to_ignore.add(line.strip()) 
        else:
            logger.info("No ignore_list.txt yet, this will be populated once the pages are parsed")


                    
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
                # Count how many links are here, if half are missing after refresh we'll assume something went wrong
                count_before_reload=len(await get_links(page))
                page_title=await page.title() 
                page_url = page.url.split('?')[0]


                
                logger.info("Reloading "+page_url)
                await page.reload()

                logger.info("Waiting a bit for the page to load")
                await asyncio.sleep(5)


                logger.info("Fetching all links present on page "+page_url)
                links = await get_links(page)

                new_links=[[url,text] for [url, text] in links if url not in urls_to_ignore]

                with open(ignore_list,'a') as file:
                    for [url, text] in new_links:  
                        file.write(url+'\n')
                        urls_to_ignore.add(url)

                logger.info(f"Found {len(links)} of which {len(new_links)} are new.")

                if len(links)<count_before_reload/2:
                    logger.info(f"{page_title} ({page_url}) has very few links, alert needed")
                    pages_with_issues+=1
                    mail_body  += f'\n{page.title()} ({page.url}) had {count_before_reload} links before reloade and now only {len(links)}\n'
                
                elif page_url not in urls_to_ignore:
                    logger.info(f"{page_title} ({page_url}) is new, user probably just opened it, let's add it and its links to ignore list")
                    # The page we're on is new, we'll probably get many new links but there's no need to notify the user
                    
                    with open(ignore_list,'a') as file:
                        file.write(page_url+'\n')
                        urls_to_ignore.add(page_url)

                elif len(new_links)>0 : 
                    logger.info(f"{page_title} ({page_url}) has {len(new_links)} new links, user will be notified")
                    list= '\n'.join(['- '+title+' : '+url for [url, title] in new_links])
                    total_new_links+=len(new_links)
                    mail_body+= f'{page.title()} ({page.url}) has {len(new_links)} new links : \n{list}\n\n'
                else :
                    logger.info(f"{page_title} ({page_url}) has {len(links)} links but nothing new")

            if mail_body!="":
                logger.info("New links found, sending email.") 
                subject= "Jobalerts : {pages_with_issues} page issue" if pages_with_issues>0 else f'Jobalerts : {len(new_links)} new links found'
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
    return page.evaluate("([]) => Array.from(document.links).map(item => [new URL(item.href, document.baseURI).href.split('?')[0],item.textContent])", [])
 

def send_email(subject, body): 
    sender = os.getenv("USER_GMAIL_ADRESS")
    password = os.getenv("USER_GMAIL_APP_PASSWORD").replace(" ", "")
 
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = sender
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login(sender, password)
       smtp_server.sendmail(sender, [sender], msg.as_string())
    print("Message sent!")
  

logging.basicConfig(filename='jobalerts.log', level=logging.INFO)

asyncio.run(main())
