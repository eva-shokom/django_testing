from http import HTTPStatus
from pytils.translit import slugify

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.models import Note
from notes.forms import WARNING


User = get_user_model()


class TestCreateNote(TestCase):
    TITLE = 'Название заметки'
    TEXT = 'Текст заметки'
    SLUG = 'note_slug'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Пользователь')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.success_url = reverse('notes:success')
        cls.add_url = reverse('notes:add')
        cls.form_data = {'title': cls.TITLE,
                         'text': cls.TEXT,
                         'slug': cls.SLUG}

    def test_user_can_create_note(self):
        count_before_creating = Note.objects.count()
        response = self.auth_client.post(self.add_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        count_after_creating = Note.objects.count()
        count_difference = count_after_creating - count_before_creating
        self.assertEqual(count_difference, 1)
        new_note = Note.objects.get()
        self.assertEqual(new_note.title, self.TITLE)
        self.assertEqual(new_note.text, self.TEXT)
        self.assertEqual(new_note.slug, self.SLUG)
        self.assertEqual(new_note.author, self.user)

    def test_anonymous_user_cant_create_note(self):
        count_before_creating = Note.objects.count()
        response = self.client.post(self.add_url, data=self.form_data)
        count_after_creating = Note.objects.count()
        count_difference = count_after_creating - count_before_creating
        self.assertEqual(count_difference, 0)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={self.add_url}'
        self.assertRedirects(response, expected_url)

    def test_empty_slug(self):
        count_before_creating = Note.objects.count()
        self.form_data.pop('slug')
        response = self.auth_client.post(
            self.add_url, data=self.form_data
        )
        self.assertRedirects(response, reverse('notes:success'))
        count_after_creating = Note.objects.count()
        count_difference = count_after_creating - count_before_creating
        self.assertEqual(count_difference, 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestEditDeleteNote(TestCase):
    TITLE = 'Название заметки'
    TEXT = 'Текст заметки'
    SLUG = 'note_slug'
    NEW_TITLE = 'Новое название'
    NEW_TEXT = 'Новый текст'
    NEW_SLUG = 'new_slug'

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Пользователь')
        cls.other_user = User.objects.create(username='Другой пользователь')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.note = Note.objects.create(title=cls.TITLE,
                                       text=cls.TEXT,
                                       slug=cls.SLUG,
                                       author=cls.user)
        cls.success_url = reverse('notes:success')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.form_data = {'title': cls.NEW_TITLE,
                         'text': cls.NEW_TEXT,
                         'slug': cls.NEW_SLUG}

    def test_author_can_edit_note(self):
        response = self.auth_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.NEW_TITLE)
        self.assertEqual(self.note.text, self.NEW_TEXT)
        self.assertEqual(self.note.slug, self.NEW_SLUG)

    def test_other_user_cant_edit_note(self):
        self.client.force_login(self.other_user)
        response = self.client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.TITLE)
        self.assertEqual(self.note.text, self.TEXT)
        self.assertEqual(self.note.slug, self.SLUG)

    def test_author_can_delete_note(self):
        count_before_deletion = Note.objects.count()
        response = self.auth_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
        count_after_deletion = Note.objects.count()
        count_difference = count_before_deletion - count_after_deletion
        self.assertEqual(count_difference, 1)

    def test_other_user_cant_delete_note(self):
        self.client.force_login(self.other_user)
        count_before_deletion = Note.objects.count()
        response = self.client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        count_after_deletion = Note.objects.count()
        count_difference = count_before_deletion - count_after_deletion
        self.assertEqual(count_difference, 0)

    def test_slug_cant_be_repeated(self):
        self.form_data['slug'] = self.note.slug
        add_url = reverse('notes:add')
        count_before_creating = Note.objects.count()
        response = self.auth_client.post(add_url, data=self.form_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=self.SLUG + WARNING
        )
        count_after_creating = Note.objects.count()
        count_difference = count_after_creating - count_before_creating
        self.assertEqual(count_difference, 0)
