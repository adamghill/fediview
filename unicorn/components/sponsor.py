import httpx
from django.conf import settings
from django.contrib import messages
from django_unicorn.components import UnicornView
from glom import glom

from account.models import GitHubAccount


def _get_sponsorships_as_maintainer():
    # TODO: Paginate sponsorships if there are ever more than 100

    gql = """
query {
    viewer {
        sponsorshipsAsMaintainer(first: 100, includePrivate: true, activeOnly: true) {
            nodes {
                sponsorEntity {
                    ... on User {
                        login
                    }
                }
            }
        }
    }
}
"""

    token = settings.GITHUB_PERSONAL_ACCESS_TOKEN

    res = httpx.post(
        "https://api.github.com/graphql",
        json={"query": gql},
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )

    return res.json()


def check_sponsorship(github_username):
    sponsorships_data = _get_sponsorships_as_maintainer()

    sponsor_entities = glom(
        sponsorships_data,
        ("data.viewer.sponsorshipsAsMaintainer.nodes", ["sponsorEntity"]),
    )

    # TODO: Figure out how to do this in glom, maybe Flatten?
    if list(filter(lambda s: s.get("login") == github_username, sponsor_entities)):
        return True

    return False


class SponsorView(UnicornView):
    github_username: str = ""
    has_plus: bool = False

    def hydrate(self):
        self.errors = {}

        if self.request.user.is_authenticated:
            github_account = GitHubAccount.objects.filter(
                account=self.request.user.account
            ).first()

            if github_account:
                self.github_username = github_account.username

            self.has_plus = self.request.user.account.profile.has_plus

    def check_username(self):
        if self.has_plus:
            return

        if not self.github_username:
            self.errors["username"] = "Please authorize on GitHub."

            return

        if check_sponsorship(self.github_username):
            profile = self.request.user.account.profile

            profile.has_plus = True
            profile.save()

            self.has_plus = True

            messages.success(self.request, "Thank you for sponsoring me!")
        else:
            self.errors[
                "username"
            ] = f'It does not appear that {self.github_username} is sponsoring "adamghill". Please contact support@adamghill.com if this a mistake.'
