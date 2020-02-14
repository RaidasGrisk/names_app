from data_sources.google_scrape import get_google_search_scrape
from googleapiclient.discovery import build
from collections import Counter, OrderedDict
from private import GOOGLE_KEYS

from find_job_titles import Finder

from googletrans import Translator


def google_search_scrape(person_name, exact_match, pages=1):

    def reorganize_data(search_results):
        data = {'items': [], 'totalResults': search_results[0].number_of_results}
        for item in search_results:

            # little trick to fix bug inside name
            # it parses the text above the title containing a link
            # lets remove this as this is not what we want
            # point_of_remove = [i for i in item.link.split('/') if len(i) > 1][-1]
            # item.name = item.name.split(point_of_remove)[-1]

            data['items'].append({'displayLink': item.link,
                                  'snippet': item.description,
                                  'title': item.name})
        return data

    search_results = get_google_search_scrape(person_name, exact_match)
    search_results = reorganize_data(search_results)

    return search_results


def google_search(person_name, num_pages=5):
    my_api_key = GOOGLE_KEYS['my_api_key']
    my_cse_id = GOOGLE_KEYS['my_cse_id']
    service = build("customsearch", "v1", developerKey=my_api_key)

    search_results = service.cse().list(q=person_name, cx=my_cse_id).execute()

    def process_google_response(google_response):
        output = {'totalResults': google_response['queries']['request'][0]['totalResults']}
        fields_to_parse_from_items = ['title',
                                      'displayLink',
                                      'snippet']
        parsed_items = []
        for item in google_response['items']:
            parsed_item_fields = {}
            for data_field in fields_to_parse_from_items:
                # print(data_field, item[data_field])
                parsed_item_fields[data_field] = item[data_field]
            parsed_items.append(parsed_item_fields)

        output['items'] = parsed_items

        return output

    search_results = process_google_response(search_results)

    return search_results


def google_translate(search_results):
    # https://github.com/ssut/py-googletrans
    # TODO: do in one batch by giving an array

    # collect items to translate
    snippets = [item['snippet'] for item in search_results['items']]
    titles = [item['title'] for item in search_results['items']]
    text_to_translate = snippets + titles

    # translate
    translator = Translator()
    translated = [item.text for item in translator.translate(text_to_translate, dest='en')]

    # ungroup
    snippets_translated = translated[:len(snippets)]
    titles_translated = translated[len(snippets):]

    # assign
    for item, snippet, title in zip(search_results['items'], snippets_translated, titles_translated):
        item['snippet'] = snippet
        item['title'] = title

    return search_results


def get_google_data_analytics(search_results, nlp_models, person_name, ingore_name):

    def clean_text(text, nlp_models, person_name, ingore_name=True):
        import re
        import unicodedata

        output = text.replace('\n', ' ')
        output = re.sub(r'([^\s\w]|_)+', ' ', output).lower()  # remove non alphanum chars
        output = re.sub(r'[0-9]', ' ', output)  # remove numbers
        output = ''.join((c for c in unicodedata.normalize('NFD', output) if unicodedata.category(c) != 'Mn'))  # weird chars to latin
        output = output.replace('  ', ' ')  # replace double spaces with space
        output = re.sub(r'\b[a-z]{1,2}\b', ' ', output)  # remove words that are 2 or less chars

        # remove stop words
        nlp = nlp_models['EN']
        output = ' '.join(token.lemma_ for token in nlp(output) if not token.is_stop)

        # remove name and surename
        # TODO:  liet raides ir lot, etc, previous cleaning should apply to this
        if ingore_name:
            for name_part in person_name.split():
                name_part = name_part.lower()
                output = output.replace(name_part, '')

        return output

    # translate
    search_results = google_translate(search_results)

    # combine into one string
    text_items_combined = ' '.join([item['snippet'] + ' ' + item['title'] for item in search_results['items']])

    # extract job titles
    job_titles = []
    try:
        finder = Finder()
        job_titles = finder.findall(text_items_combined)
        job_titles = list(set([title.match for title in job_titles]))
    except RuntimeError:
        print('Job Title finder failed')

    # extract entities
    from helpers import get_entities
    nlp = nlp_models['EN']
    entities = get_entities(text_items_combined, {'EN': nlp})

    # count words
    text_items_cleaned = clean_text(text_items_combined, nlp_models, person_name)
    frequent_words = OrderedDict(Counter(text_items_cleaned.split()).most_common()[:25])

    return {'job_titles': job_titles, 'entities': entities, 'frequent_words': frequent_words}

# from other.main import pretty_print_json
# pretty_print_json(search_results)
