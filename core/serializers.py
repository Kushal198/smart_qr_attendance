import datetime
from datetime import date
import pyotp
from django.core.exceptions import BadRequest
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from .models import Attendance, Course, AttendanceClass,Student,Teacher,Class
from django.contrib.auth.models import User


class ReadUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'first_name', 'last_name')


class ClassIdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ('department', 'semester')


class TeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = ('id', 'name', 'department',)


class ReadCourseSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer()
    class_id = ClassIdSerializer()

    class Meta:
        model = Course
        fields = ('id', 'name', 'teacher', 'code', 'class_id')


class WriteAttendanceSerializer(serializers.ModelSerializer):
    student = serializers.HiddenField(default=serializers.CurrentUserDefault())
    date = serializers.HiddenField(default=datetime.date.today)

    class Meta:
        model = Attendance
        fields = (
            'status',
            'date',
            'student',
        )

    def get_serializer_context(self):
        return self.context['request'].data

    def get_default(self):
        return self.context['request'].user.student

    def create(self, validated_data):
        request_data = dict(self.get_serializer_context())
        user = self.get_default()
        code = pyotp.parse_uri(request_data['otpauthurl'])
        try:
            attendance_class = AttendanceClass.objects.get(secret=code.secret)
            time1 = attendance_class.created_at.replace(tzinfo=None)
            time2 = datetime.datetime.now()
            print(time1, '', time2)
            diff = time2 - time1
            if(diff.total_seconds()/60 > 60):
                raise Http404
            course = attendance_class.course
            instance = get_object_or_404(Attendance,student=user, course=course, date=date.today())
            instance.status = validated_data['status']
            instance.save()
            return instance
        except AttendanceClass.DoesNotExist:
            raise Http404


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = ('roll_number', 'name',)


class ReadAttendanceSerializer(serializers.ModelSerializer):
    student = StudentSerializer()
    course = ReadCourseSerializer()

    class Meta:
        model = Attendance
        fields = (
            'id',
            'course',
            'student',
            'attendance_class',
            'date',
            'status',
        )
        read_only_fields = fields


class CourseEnrollSerializer(serializers.ModelSerializer):
    # student = StudentSerializer(many=True, read_only=True)
    class Meta:
        model = Course
        fields = ('id', 'name', 'teacher','class_id', 'students',)
        depth = 1

