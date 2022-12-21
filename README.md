# fedigest

Get a digest of popular posts and boosts from your Mastodon (fediverse) timeline.

## Run

1. `cp .env.example .env` and update the values in `.env`
1. `poetry install`
1. `poe r`
1. Go to localhost:8777

## Acknowledgements

- Uses a fork of https://github.com/hodgesmr/mastodon_digest for the actual algorithm
- [Marx](https://mblode.github.io/marx/) for classless CSS
- [Unicorn](https://www.django-unicorn.com) for the SPA feelings
- [Django](https://www.djangoproject.com/) for everything else
