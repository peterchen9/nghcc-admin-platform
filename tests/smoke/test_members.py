from modules.eureka.attendance import get_attendance_summary
from modules.eureka.models import CheckinRecord, Member


def test_members_page_is_available(logged_in_client):
    response = logged_in_client.get("/eureka/")

    assert response.status_code == 200


def test_members_table_has_restored_data():
    assert Member.objects.count() >= 7895


def test_checkin_records_model_maps_restored_data():
    assert CheckinRecord.objects.count() >= 130000


def test_realtime_attendance_summary_uses_checkin_records():
    summary = get_attendance_summary(7)

    assert "checkin_records" in summary["source_label"]
    assert summary["display"] == "2024:94% 2025:71% 2026:50%"
    assert len(summary["blocks"]) == 52
    assert str(summary["latest_source_date"]) == "2026-05-17"
    assert "percent_year" not in summary
