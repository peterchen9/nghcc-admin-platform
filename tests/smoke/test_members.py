from modules.eureka.models import Member
from modules.eureka.attendance import get_attendance_summary


def test_members_page_is_available(logged_in_client):
    response = logged_in_client.get("/eureka/")

    assert response.status_code == 200


def test_members_table_has_restored_data():
    assert Member.objects.count() >= 7895


def test_realtime_attendance_summary_uses_checkin_records():
    summary = get_attendance_summary(7)

    assert summary["source_label"] == "即時計算：checkin_records 主日報到"
    assert summary["yearly"]
    assert summary["blocks"]
    assert "percent_year" not in summary
