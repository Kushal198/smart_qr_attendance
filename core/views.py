from datetime import date
import pyotp
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView,DeleteView
from rest_framework import viewsets, status
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from .models import Course, Attendance, AttendanceClass, Teacher, Department, Student
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
import qrcode
import qrcode.image.svg
from io import BytesIO
from rest_framework.authtoken.models import Token
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


@login_required
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
                r.save()
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


class AttendanceModelViewSet(ModelViewSet, LoginRequiredMixin):
    def get_queryset(self):
        return Attendance.objects.filter(student=self.request.user.student)

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ReadAttendanceSerializer
        return WriteAttendanceSerializer


@login_required
def logout_view(request):
    logout(request)
    return redirect('%s?next=%s' % (settings.LOGIN_URL, 'accounts/login/'))


class CourseEnrollViewSet(viewsets.ModelViewSet,LoginRequiredMixin):
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


class ObtainAuthTokenEdit(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                       context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.pk,
            'name': user.student.name,
            'email': user.email
        })

@login_required
def filterDateApi(request,pk):
    context = {}
    queryset = Student.objects.raw('''SELECT roll_number,date,name,status,course_id 
    FROM core_student A 
    LEFT JOIN (SELECT * FROM core_attendance WHERE date=CURRENT_DATE AND course_id=%s)as B 
    ON A.roll_number=B.student_id'''%pk)
    print(queryset)
    context['object_list'] = queryset
    return render(request, 'courses/manage/attendance/list.html', context=context)


# class AddStudents(CreateView):
#     template_name = 'courses/manage/student/add.html'
#     form_class = StudentCreateForm
#
#     # def form_valid(self, form):
#     #     self.object = form.save(commit=False)
#     #     self.object.user = self.request.user
#     #     self.object.save()
#     #     return HttpResponseRedirect(self.get_success_url())
#
#     def get_initial(self, *args, **kwargs):
#         initial = super(AddStudents, self).get_initial(**kwargs)
#         initial['title'] = 'My Title'
#         return initial
#
#     # def get_form_kwargs(self, *args, **kwargs):
#     #     kwargs = super(AddStudents, self).get_form_kwargs(*args, **kwargs)
#     #     kwargs['user'] = self.request.user
#     #     return kwargs

def get_student_detail(request, pk,course_id):
    context = {}
    date__gte = request.GET.get('date__gte')
    date__lt = request.GET.get('date__lt')
    if date__lt is None or date__gte is None:
        queryset = Attendance.objects.filter(student_id=pk,course=course_id)
    else:
        queryset = Attendance.objects.filter(
            date__gte=date__gte,
            date__lte=date__lt,
            course=course_id,
            student_id=pk)
    context['object_list'] = queryset
    return render(request, 'courses/manage/attendance/student_attendance.html', context=context)