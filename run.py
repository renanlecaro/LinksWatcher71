import asyncio
from playwright.async_api import async_playwright 
from pathlib import Path
import sys
import logging
import json


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

            logger.info("Waiting a bit for all pages to load")
            await asyncio.sleep(10)
    
            new_links = [] 

            for page in context.pages:

                page_title=await page.title() 

                logger.info("Fetching all links present on page "+clean(page.url))
                links = await page.evaluate("([]) => Array.from(document.links).map(item => [new URL(item.href, document.baseURI).href,item.textContent])", [])

                logger.info(f"Found {len(links)} links, checking against ignore_list.")
                with open(ignore_list,'a') as file:
                    for [url, text] in links:
                        url=clean(url)

                        if url not in urls_to_ignore:
                            new_links.append({'link_url':url, 'link_text':text,  'page_url' : page.url, 'page_title':page_title}) 
                            file.write(url+'\n')
                            urls_to_ignore.add(url)
                            logger.info(url+" is new, user will be alerted.")
            
            if len(new_links):
                logger.info("New links found : "+json.dumps(new_links)) 
            else:
                logger.info("No new links") 

            logger.info("Saving open tabs to load then next time the script starts") 
            with open(tabs_list,'w') as file:
                file.write('\n'.join([page.url for page in context.pages if page.url != 'about:blank' ]))

            wait_seconds = 20
            logger.info(f"Waiting {wait_seconds} seconds before checking for change")
            await asyncio.sleep(wait_seconds)

            logger.info("Reloading all pages")
            for page in context.pages:
                logger.info("Reloading "+clean(page.url))
                await page.reload()


  
def clean(url):    
    return url.split('?')[0]


def log(text):    
    url.split('?')[0]
        
 
logging.basicConfig(filename='jobalerts.log', level=logging.INFO)

asyncio.run(main())
