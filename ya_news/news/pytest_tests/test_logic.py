from http import HTTPStatus
import pytest
from pytest_django.asserts import assertRedirects, assertFormError

from django.urls import reverse

from news.models import Comment
from news.forms import WARNING


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, news, form_data):
    count_before_creating = Comment.objects.count()
    url = reverse('news:detail', args=(news.id,))
    client.post(url, data=form_data)
    count_after_creating = Comment.objects.count()
    count_difference = count_after_creating - count_before_creating
    assert count_difference == 0


def test_user_can_create_comment(author_client, news, form_data, author):
    count_before_creating = Comment.objects.count()
    url = reverse('news:detail', args=(news.id,))
    response = author_client.post(url, data=form_data)
    assertRedirects(response, f'{url}#comments')
    count_after_creating = Comment.objects.count()
    count_difference = count_after_creating - count_before_creating
    assert count_difference == 1
    comment = Comment.objects.get()
    assert comment.text == form_data['text']
    assert comment.news == news
    assert comment.author == author


def test_user_cant_use_bad_words(author_client, news, bad_words_data):
    count_before_creating = Comment.objects.count()
    url = reverse('news:detail', args=(news.id,))
    response = author_client.post(url, data=bad_words_data)
    assertFormError(
        response,
        form='form',
        field='text',
        errors=WARNING
    )
    count_after_creating = Comment.objects.count()
    count_difference = count_after_creating - count_before_creating
    assert count_difference == 0


def test_author_can_edit_comment(
    author_client, author, news, comment, form_data
):
    edit_url = reverse('news:edit', args=(comment.id,))
    news_url = reverse('news:detail', args=(news.id,))
    url_to_comments = news_url + '#comments'
    response = author_client.post(edit_url, data=form_data)
    assertRedirects(response, url_to_comments)
    comment.refresh_from_db()
    assert comment.text == form_data['text']
    assert comment.news == news
    assert comment.author == author


def test_user_cant_edit_comment_of_another_user(
    admin_client, comment, form_data
):
    edit_url = reverse('news:edit', args=(comment.id,))
    response = admin_client.post(edit_url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment_from_db = Comment.objects.get(id=comment.id)
    assert comment.text == comment_from_db.text
    assert comment.news == comment_from_db.news
    assert comment.author == comment_from_db.author


def test_author_can_delete_comment(author_client, comment, news):
    count_before_deletion = Comment.objects.count()
    delete_url = reverse('news:delete', args=(comment.id,))
    news_url = reverse('news:detail', args=(news.id,))
    url_to_comments = news_url + '#comments'
    response = author_client.delete(delete_url)
    assertRedirects(response, url_to_comments)
    count_after_deletion = Comment.objects.count()
    count_difference = count_before_deletion - count_after_deletion
    assert count_difference == 1


def test_user_cant_delete_comment_of_another_user(admin_client, comment):
    count_before_deletion = Comment.objects.count()
    delete_url = reverse('news:delete', args=(comment.id,))
    response = admin_client.delete(delete_url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    count_after_deletion = Comment.objects.count()
    count_difference = count_before_deletion - count_after_deletion
    assert count_difference == 0
