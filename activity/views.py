import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)
from django.shortcuts import redirect, reverse
from django_q.tasks import async_task, fetch
from fbv.views import render_html

from activity.indexer import index_posts
from activity.models import Acct, Post

logger = logging.getLogger(__name__)


SEARCH_LIMIT = 100


@login_required
@render_html("activity/activity.html")
def activity(request):
    assert request.user.account.profile.has_plus, "Plus is required"

    task_id = request.GET.get("refresh")
    show_refresh_message = False

    if task_id:
        show_refresh_message = True

        task = fetch(task_id)

        if task:
            if task.success or task.stopped:
                return redirect("activity:activity")
        else:
            show_refresh_message = False

    account = request.user.account
    profile = account.profile

    posts_indexed_count = None
    replies_indexed_count = None

    acct = Acct.objects.filter(account=account).first()

    if acct:
        posts = acct.posts.all()

        posts_indexed_count = posts.count()
        replies_indexed_count = posts.filter(reply_id__isnull=False).count()

    return {
        "profile": profile,
        "posts_indexed_count": posts_indexed_count,
        "replies_indexed_count": replies_indexed_count,
        "show_refresh_message": show_refresh_message,
    }


@login_required
@render_html("activity/search.html")
def search(request):
    profile = request.user.account.profile
    assert profile.has_plus, "Plus is required"

    posts = None
    query = request.POST.get("query") or request.GET.get("q")

    if request.is_post:
        assert (
            profile.indexing_type == profile.IndexingType.CONTENT
        ), "Content indexing type is required"

        url = reverse("activity:search")
        url = f"{url}?q={query}"

        return redirect(url)

    if query:
        vector = SearchVector("text_content")
        search_query = SearchQuery(query)

        posts = (
            Post.objects.filter(acct__account__profile=profile)
            .annotate(similarity=TrigramSimilarity("text_content", query))
            .filter(similarity__gte=0.04)
            .annotate(rank=SearchRank(vector, search_query))
            .order_by("-rank", "-similarity", "-created_at")[:SEARCH_LIMIT]
        )

    # TODO: Add pagination to results

    return {"posts": posts, "query": query}


@login_required
def refresh(request):
    assert request.user.account.profile.has_plus, "Plus is required"

    task_id = async_task(index_posts, request.user.account.profile)
    logger.info(f"Refresh indexing posts with task id: {task_id}")

    messages.success(request, "Start to index posts")

    url = reverse("activity:activity")
    url = f"{url}?refresh={task_id}"

    return redirect(url)


@login_required
def delete(request):
    # Don't check for `has_plus` in the off chance that someone still has posts, but no plus anymore
    Post.objects.filter(acct__account=request.user.account).delete()

    messages.success(request, "Posts removed from index")
    return redirect("/")
