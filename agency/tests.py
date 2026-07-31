from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from agency.models import Newspaper, Topic


class BaseAgencyTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_model = get_user_model()

        cls.admin = cls.user_model.objects.create_superuser(
            username='admin',
            password='admin12345',
            email='admin@example.com',
            years_of_experience=10,
        )

        cls.editor = cls.user_model.objects.create_user(
            username='editor',
            password='editor12345',
            email='editor@example.com',
            years_of_experience=3,
        )

        cls.other_editor = cls.user_model.objects.create_user(
            username='other_editor',
            password='other12345',
            email='other@example.com',
            years_of_experience=5,
        )

        cls.topic = Topic.objects.create(name='Politics')

        cls.editor_newspaper = Newspaper.objects.create(
            title='Editor newspaper',
            content='Editor newspaper content',
            publish_date=timezone.now(),
        )
        cls.editor_newspaper.topics.add(cls.topic)
        cls.editor_newspaper.publishers.add(cls.editor)

        cls.other_newspaper = Newspaper.objects.create(
            title='Other newspaper',
            content='Other newspaper content',
            publish_date=timezone.now() - timedelta(days=1),
        )
        cls.other_newspaper.topics.add(cls.topic)
        cls.other_newspaper.publishers.add(cls.other_editor)


class AuthenticationTests(BaseAgencyTestCase):
    def test_anonymous_user_cannot_open_newspaper_list(self):
        response = self.client.get(reverse('agency:newspaper-list'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response.url)

    def test_authenticated_editor_can_open_newspaper_list(self):
        self.client.force_login(self.editor)

        response = self.client.get(reverse('agency:newspaper-list'))

        self.assertEqual(response.status_code, 200)


class NewspaperCreateTests(BaseAgencyTestCase):
    def setUp(self):
        self.create_url = reverse('agency:newspaper-create')

    def test_editor_can_open_newspaper_create_page(self):
        self.client.force_login(self.editor)

        response = self.client.get(self.create_url)

        self.assertEqual(response.status_code, 200)

    def test_admin_can_open_newspaper_create_page(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.create_url)

        self.assertEqual(response.status_code, 200)

    def test_publishers_field_hidden_from_editor(self):
        self.client.force_login(self.editor)

        response = self.client.get(self.create_url)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('publishers', response.context['form'].fields)

    def test_publishers_field_available_to_admin(self):
        self.client.force_login(self.admin)

        response = self.client.get(self.create_url)

        self.assertEqual(response.status_code, 200)
        self.assertIn('publishers', response.context['form'].fields)

    def test_editor_becomes_publisher_after_creation(self):
        self.client.force_login(self.editor)

        response = self.client.post(
            self.create_url,
            {
                'title': 'Created by editor',
                'content': 'Some newspaper content',
                'publish_date': timezone.localdate().isoformat(),
                'topics': [self.topic.pk],
            },
        )

        self.assertEqual(response.status_code, 302)

        newspaper = Newspaper.objects.get(title='Created by editor')

        self.assertTrue(newspaper.publishers.filter(pk=self.editor.pk).exists())
        self.assertEqual(newspaper.publishers.count(), 1)

    def test_editor_cannot_assign_another_publisher_on_creation(self):
        self.client.force_login(self.editor)

        self.client.post(
            self.create_url,
            {
                'title': 'Publisher injection attempt',
                'content': 'Some newspaper content',
                'publish_date': timezone.localdate().isoformat(),
                'topics': [self.topic.pk],
                'publishers': [self.other_editor.pk],
            },
        )

        newspaper = Newspaper.objects.get(title='Publisher injection attempt')

        self.assertTrue(newspaper.publishers.filter(pk=self.editor.pk).exists())
        self.assertFalse(newspaper.publishers.filter(pk=self.other_editor.pk).exists())

    def test_admin_can_choose_publishers(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            self.create_url,
            {
                'title': 'Created by admin',
                'content': 'Admin newspaper content',
                'publish_date': timezone.localdate().isoformat(),
                'topics': [self.topic.pk],
                'publishers': [
                    self.editor.pk,
                    self.other_editor.pk,
                ],
            },
        )

        self.assertEqual(response.status_code, 302)

        newspaper = Newspaper.objects.get(title='Created by admin')

        self.assertQuerySetEqual(
            newspaper.publishers.order_by('pk'),
            [self.editor, self.other_editor],
        )


class NewspaperPermissionTests(BaseAgencyTestCase):
    def test_editor_can_open_own_newspaper_update_page(self):
        self.client.force_login(self.editor)

        response = self.client.get(
            reverse(
                'agency:newspaper-update',
                args=[self.editor_newspaper.pk],
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_editor_cannot_open_other_newspaper_update_page(self):
        self.client.force_login(self.editor)

        response = self.client.get(
            reverse(
                'agency:newspaper-update',
                args=[self.other_newspaper.pk],
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_editor_can_open_own_newspaper_delete_page(self):
        self.client.force_login(self.editor)

        response = self.client.get(
            reverse(
                'agency:newspaper-delete',
                args=[self.editor_newspaper.pk],
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_editor_cannot_delete_other_newspaper(self):
        self.client.force_login(self.editor)

        response = self.client.post(
            reverse(
                'agency:newspaper-delete',
                args=[self.other_newspaper.pk],
            )
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Newspaper.objects.filter(pk=self.other_newspaper.pk).exists())

    def test_admin_can_update_any_newspaper(self):
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse(
                'agency:newspaper-update',
                args=[self.other_newspaper.pk],
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_admin_can_delete_any_newspaper(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                'agency:newspaper-delete',
                args=[self.other_newspaper.pk],
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(Newspaper.objects.filter(pk=self.other_newspaper.pk).exists())


class TopicPermissionTests(BaseAgencyTestCase):
    def test_editor_cannot_open_topic_create_page(self):
        self.client.force_login(self.editor)

        response = self.client.get(reverse('agency:topic-create'))

        self.assertEqual(response.status_code, 403)

    def test_editor_cannot_open_topic_update_page(self):
        self.client.force_login(self.editor)

        response = self.client.get(
            reverse(
                'agency:topic-update',
                args=[self.topic.pk],
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_editor_cannot_delete_topic(self):
        self.client.force_login(self.editor)

        response = self.client.post(
            reverse(
                'agency:topic-delete',
                args=[self.topic.pk],
            )
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Topic.objects.filter(pk=self.topic.pk).exists())

    def test_admin_can_open_topic_create_page(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('agency:topic-create'))

        self.assertEqual(response.status_code, 200)

    def test_admin_can_create_topic(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('agency:topic-create'),
            {'name': 'Technology'},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Topic.objects.filter(name='Technology').exists())


class RedactorPermissionTests(BaseAgencyTestCase):
    def test_editor_can_update_own_profile(self):
        self.client.force_login(self.editor)

        response = self.client.get(
            reverse(
                'agency:redactor-update',
                args=[self.editor.pk],
            )
        )

        self.assertEqual(response.status_code, 200)

    def test_editor_cannot_update_other_profile(self):
        self.client.force_login(self.editor)

        response = self.client.get(
            reverse(
                'agency:redactor-update',
                args=[self.other_editor.pk],
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_editor_can_update_own_experience(self):
        self.client.force_login(self.editor)

        response = self.client.post(
            reverse(
                'agency:redactor-update-experience',
                args=[self.editor.pk],
            ),
            {'years_of_experience': 7},
        )

        self.assertEqual(response.status_code, 302)

        self.editor.refresh_from_db()
        self.assertEqual(
            self.editor.years_of_experience,
            7,
        )

    def test_editor_cannot_create_redactor(self):
        self.client.force_login(self.editor)

        response = self.client.get(reverse('agency:redactor-create'))

        self.assertEqual(response.status_code, 403)

    def test_editor_cannot_delete_redactor(self):
        self.client.force_login(self.editor)

        response = self.client.post(
            reverse(
                'agency:redactor-delete',
                args=[self.other_editor.pk],
            )
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            self.user_model.objects.filter(pk=self.other_editor.pk).exists()
        )

    def test_admin_can_open_redactor_create_page(self):
        self.client.force_login(self.admin)

        response = self.client.get(reverse('agency:redactor-create'))

        self.assertEqual(response.status_code, 200)

    def test_admin_can_delete_redactor(self):
        user_to_delete = self.user_model.objects.create_user(
            username='delete_me',
            password='delete12345',
        )

        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                'agency:redactor-delete',
                args=[user_to_delete.pk],
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.user_model.objects.filter(pk=user_to_delete.pk).exists())
