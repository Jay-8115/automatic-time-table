from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, BooleanField, SubmitField, SelectMultipleField, PasswordField
from wtforms.validators import DataRequired, Email, Optional, Length, EqualTo, ValidationError
from wtforms.widgets import CheckboxInput, ListWidget
from models import User

class ClassForm(FlaskForm):
    name = StringField('Class Name', validators=[DataRequired(), Length(max=100)])
    submit = SubmitField('Add Class')

class SectionForm(FlaskForm):
    name = StringField('Section Name', validators=[DataRequired(), Length(max=50)])
    submit = SubmitField('Add Section')

class TeacherForm(FlaskForm):
    name = StringField('Teacher Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Email', validators=[Optional(), Email(), Length(max=100)])
    department = StringField('Department', validators=[Optional(), Length(max=100)])
    submit = SubmitField('Add Teacher')

class CourseForm(FlaskForm):
    name = StringField('Course Name', validators=[DataRequired(), Length(max=100)])
    code = StringField('Course Code', validators=[Optional(), Length(max=20)])
    is_lab = BooleanField('Is Lab Course')
    is_lecture = BooleanField('Is Lecture Course')
    lab_hours = StringField('Weekly Lab Hours', validators=[Optional()])
    lecture_hours = StringField('Weekly Lecture Hours', validators=[Optional()])
    submit = SubmitField('Add Course')

class CourseAssignmentForm(FlaskForm):
    class_id = SelectField('Class', validators=[DataRequired()], coerce=int)
    teacher_id = SelectField('Teacher', validators=[DataRequired()], coerce=int)
    course_id = SelectField('Course', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Assign Course')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', 
                                    validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is already taken. Please choose a different one.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is already registered. Please use a different one.')
