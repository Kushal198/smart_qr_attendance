from django.urls import path,include
from django.views.generic import RedirectView
from rest_framework import routers
from django.contrib.auth import views as auth_views
from rest_framework.authtoken.views import obtain_auth_token

from . import views

router = routers.SimpleRouter()
#
router.register(r'attendances', views.AttendanceModelViewSet, basename="attendance")
router.register(r'courses', views.CourseEnrollViewSet, basename="course")


urlpatterns = [
    path('',RedirectView.as_view(url='/course/mine')),
    path('api-auth/', include('rest_framework.urls')),
    path('login/', views.ObtainAuthTokenEdit.as_view(), name='obtain-auth-token'),
    path('accounts/logout/', views.logout_view, name='logout'),
    path('course/mine/', views.ManageCourseListView.as_view(), name='manage_course_list'),
    path('create/', views.CourseCreateView.as_view(), name='course_create'),
    path('<pk>/edit/', views.CourseUpdateView.as_view(), name='course_edit'),
    path('<pk>/delete/', views.CourseDeleteView.as_view(), name='course_delete'),
    path('<pk>/course-attendance/', views.filterDateApi, name='manage_attendance_list'),
    path('<pk>/generate-qr/', views.generateQRCode, name='create_qr_code'),
    path('<pk>/<course_id>/student-detail/', views.get_student_detail, name='get_student_detail'),
    path('<pk>/course-view-attendance/', views.DetailStudentCourseAttendance.as_view(), name='course_attendance')
] + router.urls