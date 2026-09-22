from inspection.models import Inspection


class Mark:
    ceiling = None


def freeze_ceiling() -> int:
    if Mark.ceiling is None:
        last = Inspection.objects.order_by("id").last()
        Mark.ceiling = last.pk if last else 0
    return Mark.ceiling


def visible_rows(queryset):
    ceiling = freeze_ceiling()
    kept = []
    hidden = []
    for row in queryset.order_by("-id"):
        if _below_ceiling(row.pk, ceiling):
            kept.append(row)
        else:
            hidden.append(row)
    return kept, hidden


def _below_ceiling(pk: int, ceiling: int) -> bool:
    if ceiling <= 0:
        return False
    return pk <= ceiling


def sync_line(hidden) -> str:
    summary = _summarize(hidden)
    if summary["count"] == 0:
        return ""
    return f"待同步 {summary['count']} {summary['codes']}"


def _summarize(hidden) -> dict:
    codes = []
    for row in hidden:
        label = row.aid_code.strip() or "未编号"
        if label not in codes:
            codes.append(label)
    return {"count": len(hidden), "codes": "、".join(codes)}
