from django import forms
# from django.contrib.admin.widgets import AdminDateWidget
# from django.forms.fields import DateField
# from .models import Student
#
#
# class StudentCreateForm(forms.ModelForm):
#     username = forms.CharField(max_length=100)
#     DOB = forms.DateField(widget = forms.SelectDateWidget)
#
#     class Meta:
#         model = Student
#         fields = ['username','class_id','roll_number', 'name', 'sex','DOB' ]
#
#     def __init__(self, *args, **kwargs):
#         # self.user = kwargs.pop('user')
#         super(StudentCreateForm, self).__init__(*args, **kwargs)


    # def clean_title(self):
    #     title = self.cleaned_data['title']
    #     if Student.objects.filter(user=self.user, title=title).exists():
    #         raise forms.ValidationError("You have already written a book with same title.")
    #     return title