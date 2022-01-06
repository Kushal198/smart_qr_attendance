from django.db import models
from django.contrib.auth.models import User
from smart_selects.db_fields import ChainedForeignKey
import datetime
# Create your models here.

time_slots = (
    ('7:30 - 8:30', '7:30 - 8:30'),
    ('8:30 - 9:30', '8:30 - 9:30'),
    ('9:30 - 10:30', '9:30 - 10:30'),
    ('11:00 - 11:50', '11:00 - 11:50'),
    ('11:50 - 12:40', '11:50 - 12:40'),
)

DAYS_OF_WEEK = (
    ('Sunday', 'Sunday'),
    ('Monday', 'Monday'),
    ('Tuesday', 'Tuesday'),
    ('Wednesday', 'Wednesday'),
    ('Thursday', 'Thursday'),
    ('Friday', 'Friday'),
)

sex_choice = (
    ('Male', 'Male'),
    ('Female', 'Female')
)


class Department(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Class(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='classes')
    section = models.CharField(max_length=100)
    semester = models.IntegerField()

    class Meta:
        verbose_name_plural = 'classes'

    def __str__(self):
        d = Department.objects.get(name=self.department)
        return '%s: %d %s' % (d.name, self.semester, self.section)


class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE, default=1)
    roll_number = models.CharField(primary_key='True', max_length=100)
    name = models.CharField(max_length=200)
    sex = models.CharField(max_length=50, choices=sex_choice, default='Male')
    DOB = models.DateField(default='1990-01-01')

    def __str__(self):
        return self.name


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    id = models.CharField(primary_key=True, max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, default=1)
    name = models.CharField(max_length=100)
    sex = models.CharField(max_length=50, choices=sex_choice, default='Male')
    DOB = models.DateField(default='1980-01-01')

    def __str__(self):
        return self.name


class Course(models.Model):
    department = models.ForeignKey(Department, related_name='courses', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='courses')
    students = models.ManyToManyField(Student, related_name='courses_joined', blank=True)
    code = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class AssignTime(models.Model):
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    course = ChainedForeignKey(
        Course,
        chained_field='class_id',
        on_delete=models.CASCADE,
        chained_model_field='class_id',
        show_all=False,
        auto_choose=True,
        sort=True,
        null=True
        )
    period = models.CharField(max_length=50, choices=time_slots, default='11:00 - 11:50')
    day = models.CharField(max_length=15, choices=DAYS_OF_WEEK)


class AttendanceClass(models.Model):
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    course = ChainedForeignKey(
        Course,
        chained_field='class_id',
        on_delete=models.CASCADE,
        chained_model_field='class_id',
        show_all=False,
        auto_choose=True,
        sort=True,
        null=True
    )
    date = models.DateField()
    secret = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Start Attendance'
        verbose_name_plural = 'Start Attendance'

    def __str__(self):
        teacher_name = User.objects.get(id=self.teacher.id)
        course_name = Course.objects.get(name=self.course)
        return '%s : %s' % (teacher_name, course_name.code)


class Attendance(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    attendance_class = models.ForeignKey(AttendanceClass, on_delete=models.CASCADE, default=1)
    date = models.DateField(default='2021-12-30')
    status = models.BooleanField(default='True')

    def __str__(self):
        student_name = Student.objects.get(name=self.student)
        course_name = Course.objects.get(name=self.course)
        return '%s : %s' % (student_name.name, course_name.code)
