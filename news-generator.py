import torch
from pymongo import MongoClient
import datetime
import requests


def get_url_suggested_image(query):
    r = requests.get("https://api.qwant.com/api/search/images",
                     params={
                         'count': 1,
                         'q': query,
                         't': 'images',
                         'safesearch': 1,
                         'locale': 'en_US',
                         'uiv': 4
                     },
                     headers={
                         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
                     }
                     )

    response = r.json().get('data').get('result').get('items')
    urls = [r.get('media') for r in response if r['type'] == 'image']
    if len(urls) > 0:
        return urls[0]
    else:
        return ""


client = MongoClient('mongodb://localhost:27017/')
db = client.therewillbenews
news = db.news

tokenizer = torch.hub.load('huggingface/pytorch-transformers', 'tokenizer', 'gpt2-medium')
model = torch.hub.load('huggingface/pytorch-transformers', 'modelWithLMHead', 'gpt2-medium')
model.load_state_dict(torch.load('models/medium_news_model.pt', map_location=torch.device('cpu')))
model.eval()


def compose_category_id(category):
    return f"$CATEGORY$\n{category}\n$CATEGORY$"


title_id = '$TITLE$'
subtitle_id = '$SUBTITLE$'
body_id = '$BODY$'


def is_new_finished(tokens):
    new = tokenizer.decode(tokens)
    if len(new) % 50 == 0:
        print("---------")
        print(new)
        print("---------")

    title_finished = sum(title_id == word for word in new.split()) == 2
    subtitle_finished = sum(subtitle_id == word for word in new.split()) == 2
    body_finished = sum(body_id == word for word in new.split()) == 2

    return title_finished and subtitle_finished and body_finished


def save_new(tokens, category):
    new = tokenizer.decode(tokens)

    new_title = new.split(title_id)[1]
    new_subtitle = new.split(subtitle_id)[1]
    new_body = new.split(body_id)[1]

    result = news.insert_one({'title': new_title,
                              'subtitle': new_subtitle,
                              'body': new_body,
                              'category': category,
                              'date': datetime.datetime.utcnow()})
    print(result)


categories = ['politics', 'entertainment', 'queer voices',
              'business', 'comedy', 'sports', 'black voices',
              'the worldpost', 'women', 'crime', 'media',
              'weird news', 'green', 'religion', 'science', 'world news',
              'tech', 'arts & culture', 'latino voices']

max_tokens_per_new = 600
temperature = 1
topK = 30

current_categories = categories.copy()
current_category = current_categories.pop(0)
tokens = tokenizer.encode(compose_category_id(current_category))

last_past = None

with torch.no_grad():
    while True:
        if last_past == None:
            logits, past = model(torch.tensor([tokens]))
        else:
            logits, past = model(torch.tensor([tokens[-1:]]), past=last_past)

        logit = logits[0, -1]

        topk_scores, topk_indeces = torch.topk(logit, topK)

        topk_scores = topk_scores.div(temperature).softmax(0)
        topk_index = torch.multinomial(topk_scores, 1)

        sampled_token = topk_indeces[topk_index].item()

        tokens.append(sampled_token)

        last_past = past

        is_finished = is_new_finished(tokens)

        if is_new_finished(tokens):
            save_new(tokens, current_category)

            last_past = None

            if len(current_categories) == 0:
                current_categories = categories.copy()

            current_category = current_categories.pop(0)
            tokens = tokenizer.encode(compose_category_id(current_category))

        elif len(tokens) > max_tokens_per_new:
            tokens = tokenizer.encode(compose_category_id(current_category))
            last_past = None
