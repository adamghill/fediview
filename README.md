# fediview

Get a digest of popular posts and boosts from your Mastodon (fediverse) timeline.

## Run

1. [Install poetry](https://python-poetry.org/docs/#installation)
1. `cp .env.example .env` and update the values in `.env`
1. `poetry install`
1. `poetry run python manage.py 0:8777`
1. Go to localhost:8777 in your browser

## Acknowledgements

- Uses a fork of https://github.com/hodgesmr/mastodon_digest for the actual algorithm
- Uses some code from https://github.com/mauforonda/mastodon_digest for HTML/CSS styling of posts
- [mastodon.py](https://mastodonpy.readthedocs.io/) to interact with mastodon
- [Marx](https://mblode.github.io/marx/) for classless CSS
- [Unicorn](https://www.django-unicorn.com) for the SPA feelings
- [coltrane](https://coltrane.readthedocs.io) to render markdown easily
- [Django](https://www.djangoproject.com/) for everything else

