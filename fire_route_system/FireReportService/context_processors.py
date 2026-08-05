from DataAccess.models import Tbl_Notification

def unread_notifications_count(request):
    """
    Globally registers the count of unread notifications in templates.
    """
    try:
        count = Tbl_Notification.objects.filter(is_read=False).count()
    except Exception:
        count = 0
    return {
        'unread_notifications_count': count
    }
