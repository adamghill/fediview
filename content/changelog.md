---
template: www/base.html
title: Changelog
body_class: changelog
---

# Changelog

[All commits](https://github.com/adamghill/fediview/commits/main)

## 2023-05-27

- Show media in daily emails.
- Experiment with converting markdown in posts to HTML.

## 2023-05-23

- Use the mean of post's text embeddings to create profile vectors.

## 2023-05-20

- Send daily email digests.

## 2023-05-19

- Poll for results instead of blocking to handle longer timeouts.

## 2023-05-16

- GitHub Sponsor check on plus page.

## 2023-04-30

- Allow users to turn off generating recommendations.

## 2023-04-24

- Fix bug with follow button.

## 2023-04-23

- Change scope to read-only.

## 2023-04-17

- Switch background task library.

## 2023-03-25

- Add follower, following, bookmarks, and favorite counts to activity page.
- Add job to reindex posts.

## 2023-03-23

- Use custom user agent.

## 2023-03-22

- Split getting digest into steps.

## 2023-03-14

- Add indexing, activity, and search to Plus.

## 2023-02-11

- Add filter by language to the <a href="{% url 'account:account' %}">account</a> page for <a href="{% url 'www:plus' %}">Fediview Plus</a>.
![Language Filter](/static/img/screenshots/language-filter.png)

## 2023-02-02

- Add <a href="{% url 'www:plus' %}">Fediview Plus</a> page.

## 2023-01-31

- Save settings for logged-in users.

## 2023-01-19

- Add oauth login flow.

## 2023-01-07

- Split posts and boosts into tabs. Add links summary.
![Tabs](/static/img/screenshots/tabs.png)

## 2023-01-05

- Add top navigation.
![Tabs](/static/img/screenshots/top-nav.png)

## 2023-01-03

- Fix bug with empty url/token when loading from localstorage.

## 2023-01-02

- Move generating summaries to a background worker.

## 2022-12-31

- Persist *Instance URL* and *Application Token* to localstorage. [10](https://github.com/adamghill/fediview/pull/10) by [bogosj](https://github.com/bogosj)

## 2022-12-30

- Add follow buttons to posts as necessary.
![Tabs](/static/img/screenshots/follow.png)

## 2022-12-29

- Remove the need for passing in username.
![Tabs](/static/img/screenshots/no-username.png)

## 2022-12-27

- Show currently deployed version.

## 2022-12-25

- Rename to fediview and buy domain.
![Tabs](/static/img/screenshots/fediview.png)

## 2022-12-24

- Add media lightbox.
![Tabs](/static/img/screenshots/lightbox.png)

## 2022-12-22

- Remove iframe embed.
![Tabs](/static/img/screenshots/no-iframe.png)

## 2022-12-12

- Initial commit.
![Tabs](/static/img/screenshots/fedigest.png)
![Tabs](/static/img/screenshots/initial.png)
