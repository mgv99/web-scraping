import logging
import json
import requests
import time

from bs4 import BeautifulSoup
from datetime import timedelta


def get_model_urls(pages: int, headers: dict, sleep_time: int):
    """
    This function creates a list with all the model urls in
    'https://huggingface.co/models'

    :pages: number of pages to limit the scraping scope. If zero, scrap all possible pages
    :headers: custom headers used in the GET requests
    :sleep_time: time to wait between each page scrapping, in seconds
    """
    hf_url = 'https://huggingface.co'
    page = 0
    model_urls = []

    start_time = time.time()

    while True:
        # Get the url of the current page
        hf_models_url = hf_url + f'/models?p={page}&sort=downloads'
        models_page = requests.get(hf_models_url, headers=headers)
        models_soup = BeautifulSoup(models_page.content, 'html.parser')
        model_boxes = models_soup.findAll('a', class_='block p-2')
        if len(model_boxes) == 0 or (0 < pages <= page):
            # if (there are no more models) or (we scraped the specified number of pages) stop
            break
        logging.info(f"Reading page: {page}")
        for model_box in model_boxes:
            # For each model within the current page, we save its URL
            model_url = hf_url + model_box.attrs['href']
            model_urls.append(model_url)
        page += 1
        # Sleep x seconds between requests
        time.sleep(sleep_time)

    end_time = time.time()
    logging.info(f"Number of model urls stored: {len(model_urls)}")
    logging.info(f"Elapsed time:  {timedelta(seconds=end_time - start_time)}")

    return model_urls


def get_model_attributes(url: str, headers: dict):
    """
    This function will get the attributes of each model registered
    in https://huggingface.co/models given the model URL.

    :url: url of a specific model
    :headers: custom headers used in the GET requests
    """

    fields = {}
    try:
        # Get the model page
        model_page = requests.get(url, headers=headers)
        model_soup = BeautifulSoup(model_page.content, 'html.parser')
        # Get the html section where are stored the model attributes
        modelHeaderActions = model_soup.find('div', attrs={'data-target': 'ModelHeaderActions'})
        data_props = json.loads(modelHeaderActions.attrs['data-props'].replace(r'\\"', r'\"'))
        # Relevant fields to scrap
        target_fields = ['author', 'id', 'cardExists', 'lastModified', 'likes']
        for field in target_fields:
            if field in data_props['model']:
                fields[field] = data_props['model'][field]

        tag_objs = data_props['model']['tag_objs']
        # We scrap all fields stored within tag_objs
        for tag_obj in tag_objs:
            # print(tag_obj) # uncomment this to understand the structure of the attributes
            if not tag_obj['type'] in fields:
                fields[tag_obj['type']] = []
            fields[tag_obj['type']].append(tag_obj['id'])
            if tag_obj['type'] == 'pipeline_tag':
                fields['subType'] = tag_obj['subType']

        # downloads_last_month field is in another html element
        fields['downloads_last_month'] = model_soup.find('dd', class_='font-semibold').text.replace(',', '')

    except:
        # Since this process takes several hours, some models can disappear from Hugging Face since the URLs were scraped
        logging.error(f'Error while scrapping {url}')
    return fields
