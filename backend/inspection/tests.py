from django.contrib.auth.models import Group, User
from django.test import TestCase
from django.urls import reverse

from inspection.models import Inspection


class ListReadYourWritesTests(TestCase):
    def setUp(self):
        group = Group.objects.create(name="inspector")
        self.keeper = User.objects.create_user(username="keeper", password="light123456")
        self.keeper.groups.add(group)
        self.client.force_login(self.keeper)

    def _register(self, aid_code, measured, required, bearing):
        return self.client.post(
            reverse("create"),
            {
                "aid_code": aid_code,
                "measured_cd": measured,
                "required_cd": required,
                "bearing_error_deg": bearing,
            },
        )

    def test_new_rows_visible_in_list_right_after_create(self):
        # 先打开一次总表再登记：刚写入的主键也必须出现在总表数据里
        self.client.get(reverse("list"))

        ok_response = self._register("LH-100", 1400, 1200, 0.4)  # 合格
        bad_response = self._register("LH-101", 800, 1200, 0.2)  # 不合格：光强不足

        ok_row = Inspection.objects.get(aid_code="LH-100")
        bad_row = Inspection.objects.get(aid_code="LH-101")
        self.assertEqual(ok_row.verdict, "合格")
        self.assertEqual(bad_row.verdict, "不合格")

        # 登记后重定向到详情，详情地址能打开
        self.assertRedirects(ok_response, reverse("detail", args=[ok_row.pk]))
        self.assertRedirects(bad_response, reverse("detail", args=[bad_row.pk]))

        # 总表数据必须包含刚写入的主键，且不再有“待同步”提示
        response = self.client.get(reverse("list"))
        self.assertEqual(response.status_code, 200)
        listed_pks = [row.pk for row in response.context["rows"]]
        self.assertIn(ok_row.pk, listed_pks)
        self.assertIn(bad_row.pk, listed_pks)
        self.assertNotContains(response, "待同步")
