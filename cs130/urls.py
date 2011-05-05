from django.conf.urls.defaults import patterns, include, url
from cs130.eram.views import search, ip_location

# QUICK AND DIRTY IMPORT FOR DEV ENVIRONMENTS TO SERVE STATIC FILES
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('', 
    (r'^$', search),
    (r'^search/$', search),
    (r'^ip-location/$', ip_location),
)

    # Examples:
    # url(r'^$', 'cs130.views.home', name='home'),
    # url(r'^cs130/', include('cs130.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),

# QUICK AND DIRTY IMPORT FOR DEV ENVIRONMENTS TO SERVE STATIC FILES
urlpatterns += staticfiles_urlpatterns()
