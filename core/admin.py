from django.contrib import admin
from .models import Department,Class,Course,AssignTime,AttendanceClass,Attendance,Student,Teacher

# Register your models here.

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display=['name']

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['name']

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name']
    prepopulated_fields = {'slug':('name',)}

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'department', 'code', 'teacher']

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['department','semester', 'section']

@admin.register(AssignTime)
class AssignTimeAdmin(admin.ModelAdmin):
    list_display = ['course']

@admin.register(AttendanceClass)
class AttendanceClassAdmin(admin.ModelAdmin):
    list_display = ['date']

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['course','student']
    list_filter = ['date']

