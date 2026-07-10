from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import translation

from course.services.video_progress import _compute_percent, _merge_position

User = get_user_model()


class VideoProgressHelpersTests(TestCase):
    def test_merge_position_monotonic(self):
        pos, done = _merge_position(30.0, 10.0, 120.0)
        self.assertEqual(pos, 30.0)
        self.assertFalse(done)

    def test_merge_position_near_complete(self):
        pos, done = _merge_position(0.0, 118.0, 120.0)
        self.assertTrue(done)
        self.assertLessEqual(pos, 120.0)

    def test_compute_percent(self):
        self.assertEqual(_compute_percent(30, 120, False), 25)
        self.assertEqual(_compute_percent(0, 0, True), 100)


class VideoProgressAPITests(TestCase):
    def test_post_requires_student(self):
        u = User.objects.create_user(
            username="lec_api_test",
            password="pw",
            is_lecturer=True,
            is_student=False,
        )
        c = Client()
        c.force_login(u)
        translation.activate("en")
        try:
            url = reverse("api_video_progress")
        finally:
            translation.deactivate()
        r = c.post(
            url,
            data='{"video_id":1,"position_seconds":1,"duration_seconds":10}',
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 403)
