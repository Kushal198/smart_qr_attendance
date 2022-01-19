import calendar
from datetime import datetime
from collections import OrderedDict
from datetime import date, timedelta
import pyotp
from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, permission_required, user_passes_test
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView,DeleteView
from rest_framework import viewsets, status, mixins
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from .models import Course, Attendance, AttendanceClass, Teacher, Department, Student
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
import qrcode
import qrcode.image.svg
from io import BytesIO
from rest_framework.authtoken.models import Token
from .serializers import ReadAttendanceSerializer, WriteAttendanceSerializer, CourseEnrollSerializer, \
    AttendanceCourseSerializer
from django.contrib.auth.mixins import UserPassesTestMixin

class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return not self.request.user.is_superuser


class OwnerMixin(object):
    def get_queryset(self):
        # if self.request.user.is_superuser:
        #     return redirect('/accounts/login/')
        qs = super(OwnerMixin, self).get_queryset()

        return qs.filter(teacher=self.request.user.teacher)


class OwnerEditMixin(object):
    def form_valid(self, form):
        # if self.request.user.is_superuser:
        #     return redirect('/accounts/login/')
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


class ManageCourseListView(SuperuserRequiredMixin,OwnerCourseMixin, ListView, PermissionRequiredMixin):
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
@user_passes_test(lambda u: not u.is_superuser)
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


class CourseEnrollViewSet(viewsets.ModelViewSet, LoginRequiredMixin):
    serializer_class = CourseEnrollSerializer

    def get_queryset(self):
        course = Course.objects.filter(students__roll_number=self.request.user.student.roll_number)
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
@permission_required('core.view_attendance')
@user_passes_test(lambda u: not u.is_superuser)
def filterDateApi(request, pk):
    context = {}
    queryset = Student.objects.raw('''SELECT A.roll_number,B.date,A.name,B.status,B.course_id 
    FROM core_student A 
    LEFT JOIN (SELECT * FROM core_attendance WHERE date=CURRENT_DATE AND course_id=%s)as B 
    ON A.roll_number=B.student_id'''%pk)
    context['object_list'] = queryset
    context['course_id'] = pk
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
@login_required
@permission_required('core.view_attendance','core.view_attendance')
@user_passes_test(lambda u: not u.is_superuser)
def get_student_detail(request, pk,course_id):
    # print(pk,course_id)
    student_info = Student.objects.get(roll_number=pk)
    course_info = Course.objects.get(id=course_id)
    context = {}
    date__gte = request.GET.get('date__gte')
    date__lt = request.GET.get('date__lt')
    if date__lt is None or date__gte is None:
        months_in_year = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
                          'October', 'November', 'December']
        dumy = list(AttendanceClass.objects.filter(course=course_id).values_list('date',flat=True))
        years_list = []
        for d in dumy:
            year_month = str(d.year)+'-'+str(d.month)
            if(year_month not in years_list):
                years_list.append(year_month)
        new_list = []
        for y in years_list:
            split_it = y.split('-')
            mon = months_in_year[int(split_it[1])-1]
            new_list.append(mon+' '+ split_it[0])
        days = []
        class_days = []
        for i in range(1,32):
            custDate = date.today().replace(day=i)
            if(custDate in dumy):
                class_days.append(custDate.day)
            days.append(i)
        context['days'] = days
        context['months'] = new_list
        context['class_days'] = class_days
        test = list(Attendance.objects.filter(student_id=pk,course=course_id).values_list('date','status'))
        queryset = []
        for q in test:
            queryset.append({'day':q[0].day,'status':q[1] })
    else:
        queryset = Attendance.objects.filter(
            date__gte=date__gte,
            date__lte=date__lt,
            course=course_id,
            student_id=pk)
    context['object_list'] = queryset
    context['student'] = student_info
    context['course'] = course_info
    return render(request, 'courses/manage/attendance/student_attendance.html', context=context)


class DetailStudentCourseAttendance(
    mixins.RetrieveModelMixin,
    GenericAPIView,
):

    serializer_class = AttendanceCourseSerializer

    # queryset = Course.objects.all()


    # def lookup_filed(self):
    #     print(self)

    # def retrieve(self, request, *args, **kwargs):
    #     queryset = Course.objects.get(id=kwargs['pk'],students__roll_number=self.request.user.student.roll_number)
    #     print(queryset)
    #     # queryset2 = queryset.attendances.filter(student=self.request.user.student)
    #     # print(queryset.attendances.filter(student=self.request.user.student))
    #     # print(queryset2)
    #     return queryset


    def get(self, request, *args, **kwargs):
        queryset = Course.objects.get(id=kwargs['pk'], students__roll_number=self.request.user.student.roll_number)
        # print(queryset)
        queryset2 = queryset.attendances.filter(student=self.request.user.student)
        print(queryset)
        serializer = AttendanceCourseSerializer(queryset2, many=True)
        print(serializer.data)
        return Response(serializer.data)



