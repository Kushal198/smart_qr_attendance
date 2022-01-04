from datetime import date
import pyotp
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView,DeleteView
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from .models import Course, Attendance, AttendanceClass, Teacher, Department
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
import qrcode
import qrcode.image.svg
from io import BytesIO

from .serializers import ReadAttendanceSerializer, WriteAttendanceSerializer, CourseEnrollSerializer


class OwnerMixin(object):
    def get_queryset(self):
        qs = super(OwnerMixin, self).get_queryset()
        return qs.filter(teacher=self.request.user.teacher)


class OwnerEditMixin(object):
    def form_valid(self, form):
        depart = Department.objects.get(teacher=self.request.user.teacher)
        form.instance.department = depart
        form.instance.teacher = self.request.user.teacher
        return super(OwnerEditMixin, self).form_valid(form)


class OwnerCourseMixin(OwnerMixin,LoginRequiredMixin):
    model = Course
    fields = ['name', 'code']
    success_url = reverse_lazy('manage_course_list')


class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    fields = ['class_id','name', 'code',]
    success_url = reverse_lazy('manage_course_list')
    template_name = 'courses/manage/course/form.html'


class ManageCourseListView(OwnerCourseMixin, ListView):
    template_name = 'courses/manage/course/list.html'
    permission_required = 'core.view_course'


class CourseCreateView(PermissionRequiredMixin, OwnerCourseEditMixin, CreateView):
    permission_required = 'core.add_course'


class CourseUpdateView(PermissionRequiredMixin, OwnerCourseEditMixin, UpdateView):
    permission_required = 'core.change_course'


class CourseDeleteView(PermissionRequiredMixin, OwnerCourseMixin, DeleteView):
    template_name = 'courses/manage/course/delete.html'
    success_url = reverse_lazy('manage_course_list')
    permission_required = 'core.delete_course'


@login_required
def listStudentAttendance(request, pk):
    context = {}
    attendance = Attendance.objects.filter(date=date.today(), course=pk)
    context['object_list'] = attendance
    return render(request, 'courses/manage/attendance/list.html', context=context)


def generateQRCode(request, pk):
    context = {}
    if request.method == "GET":
        course = Course.objects.get(pk=pk)
        result = AttendanceClass.objects.filter(date=date.today(),course=course)
        if not result:
            instance = AttendanceClass.objects.create(class_id=course.class_id,
                                                      teacher=request.user.teacher,
                                                      course=course,
                                                      date=date.today(),
                                                      status=True)

            otpauth = pyotp.random_base32()
            temp_secret = otpauth
            instance.secret = temp_secret
            instance.save()
            course = instance.course
            students = course.students.all()
            for s in students:
                Attendance.objects.create(student=s, course=course, attendance_class=instance, date=date.today(), status=False)
            token = pyotp.TOTP(s=temp_secret, digits=6, interval=60).provisioning_uri(name='mallu_uncut@google.com', issuer_name='Secure App')
        else:
            for r in result:
                course = r.course
                students = course.students.all()
                for s in students:
                    at = Attendance.objects.filter(student=s, course=course)
                    if not at:
                        Attendance.objects.create(student=s, course=course, attendance_class=r,
                                                  date=date.today(), status=False)
            token = pyotp.TOTP(s=result[0].secret,digits=6,interval=60).provisioning_uri(name='mallu_uncut@google.com', issuer_name='Secure App')
        factory = qrcode.image.svg.SvgImage
        print(token)
        img = qrcode.make(token, image_factory=factory, box_size=20)
        stream = BytesIO()
        img.save(stream)
        context["svg"] = stream.getvalue().decode()

    return render(request, "courses/manage/attendance/qr.html", context=context)


class AttendanceModelViewSet(ModelViewSet):
    def get_queryset(self):
        return Attendance.objects.all()

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ReadAttendanceSerializer
        return WriteAttendanceSerializer


@login_required
def logout_view(request):
    logout(request)
    return redirect('%s?next=%s' % (settings.LOGIN_URL, 'accounts/login/'))


class CourseEnrollViewSet(viewsets.ModelViewSet):
    serializer_class = CourseEnrollSerializer

    def get_queryset(self):
        course = Course.objects.all()
        return course

    def create(self, request, *args, **kwargs):
        data = request.data
        course = Course.objects.get(id=data['course'])
        if course:
            course.students.add(self.request.user.student)
        course.save()
        serializer = CourseEnrollSerializer(course)
        return Response(serializer.data)
