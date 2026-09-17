# urls.py for notifications app
# لسا ما في ولا view/endpoint حقيقي لنظام الإشعارات - هو Signals + أمر
# يومي بس لهلق (راجع notifications/signals.py و
# notifications/management/commands/send_expiry_reminders.py)، مش REST
# API. urlpatterns فاضية مؤقتاً حتى ما ينكسر include() بـ CoachLink/urls.py
# (كانت ترمي ImproperlyConfigured لأنو الملف ما كان فيه urlpatterns إطلاقاً).
urlpatterns = []
