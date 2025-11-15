from django.contrib import admin
from django.urls import path, include  # <-- 'include' yahaan import karna zaroori hai
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path("__reload__/", include("django_browser_reload.urls")),
    path('', include('barber.urls')), 
]

# Yeh code media files (service images) ko development mein serve karne ke liye hai
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
