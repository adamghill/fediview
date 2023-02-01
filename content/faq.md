---
template: www/base.html
title: FAQ
---

# FAQ

## How do I generate a token?

To authorize `fediview` to look at your timeline and build the digest it requires an `Application Token`. You can remove this token at any time.

To generate a token:
1. Login to your Mastodon instance
1. Click on the *Edit profile* link
1. Click on *Development* in the sidebar navigation
1. Click the *New application* button in the top-right
1. Type in a memorable name for the token, e.g. `fediview`
1. Optional: type in the website `https://fediview.com`
1. Unselect `write` and `follow` checkboxes
1. Click the *SUBMIT* button
1. Click the `fediview` link under the *Application* header
1. Copy the giant alphanumeric string next to *Your access token*

## I thought algorithms were bad?

First off, that's more of a statement than an actual question, but... I'll allow it!

As a somewhat newer user of Mastodon myself, I understand the worry about the algorithms used to juice engagement on other social networks. However, providing access to a user-controlled summary of popular toots is *not* inherently evil. Personally, my main issue with algorithmic timelines is the corporate incentives around driving engagement to increase ad spend and the unhealthy results for society as a whole. The algorithms are a black-box and are forced on users without the ability to control or tweak them.

On the other hand, this website doesn't track what posts you click on, it doesn't tailor the results by "people like you", and it doesn't try to predict what you might click on in the future. It doesn't use ML or AI in any sense.

`fediview` is completely separate from Mastodon and not forced on anyone. It also respects other users' privacy who do not want to be included in the results via the `#nobot` hashtag.

[This website is MIT-licensed](https://github.com/adamghill/fediview) and the [original algorithm is BSD licensed](https://github.com/hodgesmr/mastodon_digest) to see the original algorithm for popular posts and boosts.

## What are the available algorithms?

- **Simple**: Weighted geometric mean of a post's boosts and favorites.
- **Simple Weighted**: Weighted geometric mean of a post's boosts and favorites where accounts with less followers are prioritized.
- **Extended Simple**: Weighted geometric mean of a post's boosts, favorites, and replies.
- **Extended Simple Weighted**: Weighted geometric mean of a post's boosts, favorites, and replies where accounts with less followers are prioritized.

## Where can I ask for a feature, report a bug, or send accolades?

Feel free to DM me [@adamghill](https://indieweb.social/@adamghill) or start a [GitHub discussion](https://github.com/adamghill/fediview/discussions).

## What data do you store?

- A background worker is used to create personalized timelines and those are cached in `redis`. Their TTL is set to 500 seconds, to that data gets automatically cleared after 500 seconds.
- Third-party, privacy-respecting analytics services are used to get a sense of traffic patterns.
- *Instance URL* and *Application Token* can optionally be stored in the user's browser by clicking a checkbox and explicitly opting in.

### Logged-in users

- The user's username and access token are stored in a database.

### Remove access

- Access for fediview to access a user's timeline can be revoked through the user's Mastodon settings page.
- Data for logged-in users can be deleted via the account page, or via a private message to https://indieweb.social/@adamghill from the user's account.

## How can people opt out of being included in these summaries?

`fediview` tries to follow Mastodon etiquette and respects accounts who want to opt out by filtering out users who have put `#nobot` or `#nobots` in their profile.

## Why can I trust you?

The [code for this website is open-source](https://github.com/adamghill/fediview) and you can inspect it to make sure I am not doing anything shady. I include the currently deployed version of the site in the footer.

You can also run this website for your personal use or use the [original offline-only script](https://github.com/hodgesmr/mastodon_digest).

## I really love this tool, how can I help?

Thanks! I've been using it for a little while and really like it, so I hope it's useful for others. The best thing you can do is spread the word -- tell your friends who are on the fediverse, toot about it, make a vision board, etc.

Some other things that would be helpful:

- [star the repo or fork the code and make improvements](https://github.com/adamghill/fediview)
- [follow me on indieweb.social](https://indieweb.social/@adamghill)
- [sign up for DigitalOcean with my referral code](https://m.do.co/c/617d629f56c0) (it helps pay for my servers)
- [sponsor me on GitHub](https://github.com/sponsors/adamghill)

But, mostly work on that vision board. Thanks.
