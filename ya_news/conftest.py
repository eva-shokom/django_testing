import pytest
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone

from news.models import News, Comment
from news.forms import BAD_WORDS


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Автор')


@pytest.fixture
def author_client(author, client):
    client.force_login(author)
    return client


@pytest.fixture
def news():
    return News.objects.create(title='Заголовок', text='Текст')


@pytest.fixture
def all_news():
    today = datetime.today()
    all_news = [
        News(
            title=f'Новость {index}',
            text='Просто текст.',
            date=today - timedelta(days=index),
        )
        for index in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ]
    return News.objects.bulk_create(all_news)


@pytest.fixture
def comment(news, author):
    return Comment.objects.create(
        news=news, author=author, text='Tекст',
    )


@pytest.fixture
def two_comments(news, author):
    now = timezone.now()
    for index in range(2):
        comment = Comment.objects.create(
            news=news, author=author, text=f'Tекст {index}',
        )
        comment.created = now + timedelta(days=index)
        comment.save()
    return Comment.objects.all()


@pytest.fixture
def comment_id_for_args(comment):
    return comment.id,


@pytest.fixture
def news_id_for_args(news):
    return news.id,


@pytest.fixture
def form_data():
    return {'text': 'Текст комментария'}


@pytest.fixture
def bad_words_data():
    return {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
