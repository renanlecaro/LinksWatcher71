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
            logger.info("Loading ingore list from ignore_list.txt")
            with open(ignore_list,'r') as file:
                for line in file:
                    urls_to_ignore.add(line.strip()) 
        else:
            logger.info("No ignore_list.txt yet, this will be populated once the pages are parsed")


                    

        while True:
    
            new_links = [] 

            for page in context.pages:

                logger.info("Fetching all links present on page "+clean(page.url))
                links = await page.evaluate("([]) => Array.from(document.links).map(item => [new URL(item.href, document.baseURI).href,item.textContent])", [])
            

                logger.info(f"Found {len(links)} links, checking against ignore set.")
                with open(ignore_list,'a') as file:
                    for [url, text] in links:
                        url=clean(url)

                        if url not in urls_to_ignore:
                            new_links.append({link_url:url, link_text:text,  page_url : page.url, page_title:page.title}) 
                            file.write(url+'\n')
                            urls_to_ignore.add(url)
                            logger.info(url+" is new, user will be alerted.")
            
            if len(new_links):
                logger.info("New links found : "+json.dumps(new_links)) 

            wait_seconds = 20
            logger.info(f"Waiting {wait_seconds} seconds before checking for change")
            await asyncio.sleep(wait_seconds)

            logger.info("Reloading all pages")
            for page in context.pages:
                logger.info("Reloading "+clean(page.url))
                await page.reload()

            
            logger.info("Waiting a bit for all pages to load")
            await asyncio.sleep(10)

  
def clean(url):    
    return url.split('?')[0]


def log(text):    
    url.split('?')[0]
        
 
logging.basicConfig(filename='jobalerts.log', level=logging.INFO)

asyncio.run(main())
