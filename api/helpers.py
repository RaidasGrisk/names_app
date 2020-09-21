import re


def get_entities(input, nlp_models):

    # get all entities
    entities = {}
    for model_lang, nlp_model in nlp_models.items():
        doc = nlp_model(input)
        if doc.ents:
            for ent in doc.ents:
                ent_str = str(ent)
                # print(model_lang, ent.text, ent.label_)
                if ent.label_ in entities.keys():
                    entities[ent.label_].add(ent_str)
                else:
                    entities[ent.label_] = {ent_str}


    # convert to decent dict
    for key, value in entities.items():
        entities[key] = list(value)

    return entities


def process_entities(entities):

    # analyze and return
    if 'PERSON' in entities.keys():

        if len(entities['PERSON']) > 1:
            print(entities['PERSON'])
            return list(entities['PERSON'])[0]
        else:
            return list(entities['PERSON'])[0]
    else:
        print('No manes here')
        return None


def get_domain_from_url(url):
    # better use: from urllib.parse import urlparse ???
    regex = '^(?:https?:\/\/)?(?:[^@\/\n]+@)?(?:www\.)?([^:\/?\n]+)'
    return re.search(regex, url)[0]


def get_api_output_head_from_input_entities(entities):

    output = {}
    if entities.get('PERSON'):
        output['input'] = entities['PERSON'][0]
        if len(entities['PERSON']) != 1:
            output['warning'] = 'Huh!? Why is there more than one person?'
    else:
        output['warning'] = 'I am built to recognize names, but I dont see any :('
        output['entities'] = list(entities.keys())

    return output