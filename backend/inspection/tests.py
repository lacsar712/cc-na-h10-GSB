"""登记后总表必须立刻包含新主键，不允许只在详情页可见。"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from inspection.models import Inspection


class NewRegistrationListVisibilityTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username="keeper", password="x")
        user.groups.add(Group.objects.create(name="inspector"))
        self.client.force_login(user)

        # 登记前已存在的历史记录
        Inspection.objects.create(
            aid_code="LH-OLD-1",
            measured_cd=100.0,
            required_cd=100.0,
            bearing_error_deg=0.0,
            verdict="合格",
            note="历史记录",
            created_by="keeper",
        )
        # 先打开一次总表：旧的水位线旁路会在这一刻冻结主键上限
        warm = self.client.get(reverse("list"))
        self.assertEqual(warm.status_code, 200)

    def _register(self, aid_code, measured_cd, required_cd, bearing_error_deg):
        response = self.client.post(
            reverse("create"),
            {
                "aid_code": aid_code,
                "measured_cd": str(measured_cd),
                "required_cd": str(required_cd),
                "bearing_error_deg": str(bearing_error_deg),
            },
        )
        row = Inspection.objects.get(aid_code=aid_code)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("detail", args=[row.pk]))
        return row

    def test_pass_and_fail_rows_both_present_in_list(self):
        passed = self._register("LH-OK-1", 120.0, 100.0, 0.5)   # 合格
        failed = self._register("LH-NG-1", 80.0, 100.0, 0.5)    # 光强不足，不合格
        self.assertEqual(passed.verdict, "合格")
        self.assertEqual(failed.verdict, "不合格")

        # 两条新记录详情页都能打开（旧缺陷下这一步恰好也通过，不能只验它）
        for row in (passed, failed):
            detail = self.client.get(reverse("detail", args=[row.pk]))
            self.assertEqual(detail.status_code, 200)

        list_response = self.client.get(reverse("list"))
        self.assertEqual(list_response.status_code, 200)

        # 关键断言：新主键必须出现在总表数据里
        visible_pks = {row.pk for row in list_response.context["rows"]}
        self.assertIn(passed.pk, visible_pks)
        self.assertIn(failed.pk, visible_pks)

        # 总表不再渲染“待同步”提示
        self.assertNotContains(list_response, "待同步")
