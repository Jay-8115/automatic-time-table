from app import db
from datetime import time, datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    """User model for authentication"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Class(db.Model):
    """Represents a class (e.g., 'Class 10', 'Class 12')"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    sections = db.relationship('Section', backref='class_obj', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Class {self.name}>"

class Section(db.Model):
    """Represents a section of a class (e.g., 'A', 'B', 'C')"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    timetable_entries = db.relationship('TimetableEntry', backref='section', lazy=True, cascade="all, delete-orphan")
    
    __table_args__ = (db.UniqueConstraint('name', 'class_id', name='unique_section_per_class'),)
    
    def __repr__(self):
        return f"<Section {self.name} of Class {self.class_id}>"

class Teacher(db.Model):
    """Represents a teacher"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    department = db.Column(db.String(100), nullable=True)
    timetable_entries = db.relationship('TimetableEntry', backref='teacher', lazy=True)
    course_assignments = db.relationship('CourseAssignment', backref='teacher', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Teacher {self.name}>"

class Course(db.Model):
    """Represents a course/subject"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=True)
    is_lab = db.Column(db.Boolean, default=False)
    is_lecture = db.Column(db.Boolean, default=True)
    lab_hours = db.Column(db.Integer, default=0)
    lecture_hours = db.Column(db.Integer, default=0)
    course_assignments = db.relationship('CourseAssignment', backref='course', lazy=True, cascade="all, delete-orphan")
    timetable_entries = db.relationship('TimetableEntry', backref='course', lazy=True)
    
    # Changed the unique constraint to only use name
    __table_args__ = (db.UniqueConstraint('name', name='unique_course_name'),)
    
    def __repr__(self):
        course_type = []
        if self.is_lab:
            course_type.append('Lab')
        if self.is_lecture:
            course_type.append('Lecture')
        return f"<Course {self.name} ({', '.join(course_type)})>"

class CourseAssignment(db.Model):
    """Represents assignment of a course to a class/section with a teacher"""
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class.id'), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    
    # Reference to the Class
    class_obj = db.relationship('Class', backref='course_assignments')
    
    __table_args__ = (
        db.UniqueConstraint('class_id', 'teacher_id', 'course_id', 
                           name='unique_course_assignment'),
    )
    
    def __repr__(self):
        return f"<CourseAssignment Class:{self.class_id} Teacher:{self.teacher_id} Course:{self.course_id}>"

class TimeSlot(db.Model):
    """Represents a time slot in the timetable"""
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_break = db.Column(db.Boolean, default=False)
    
    timetable_entries = db.relationship('TimetableEntry', backref='time_slot', lazy=True)
    
    __table_args__ = (db.UniqueConstraint('start_time', 'end_time', name='unique_time_slot'),)
    
    def __repr__(self):
        return f"<TimeSlot {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}>"

class Day(db.Model):
    """Represents a day of the week"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False, unique=True)
    timetable_entries = db.relationship('TimetableEntry', backref='day', lazy=True)
    
    def __repr__(self):
        return f"<Day {self.name}>"

class TimetableEntry(db.Model):
    """Represents an entry in the timetable"""
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    day_id = db.Column(db.Integer, db.ForeignKey('day.id'), nullable=False)
    time_slot_id = db.Column(db.Integer, db.ForeignKey('time_slot.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'), nullable=True)
    
    __table_args__ = (
        db.UniqueConstraint('section_id', 'day_id', 'time_slot_id', 
                           name='unique_timetable_entry'),
    )
    
    def __repr__(self):
        return f"<TimetableEntry Section:{self.section_id} Day:{self.day_id} TimeSlot:{self.time_slot_id}>"

# Initialize default days and time slots
def init_default_data(db):
    # Create days if they don't exist
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    for day_name in days:
        if not Day.query.filter_by(name=day_name).first():
            day = Day()
            day.name = day_name
            db.session.add(day)
    
    # Define the time slots based on requirements
    time_slots = [
        # Period 1: 7:30 - 8:25
        {"start": time(7, 30), "end": time(8, 25), "is_break": False},
        # Period 2: 8:25 - 9:20
        {"start": time(8, 25), "end": time(9, 20), "is_break": False},
        # Break 1: 9:20 - 9:50
        {"start": time(9, 20), "end": time(9, 50), "is_break": True},
        # Period 3: 9:50 - 10:45
        {"start": time(9, 50), "end": time(10, 45), "is_break": False},
        # Period 4: 10:45 - 11:40
        {"start": time(10, 45), "end": time(11, 40), "is_break": False},
        # Break 2: 11:40 - 11:50
        {"start": time(11, 40), "end": time(11, 50), "is_break": True},
        # Period 5: 11:50 - 12:45
        {"start": time(11, 50), "end": time(12, 45), "is_break": False},
        # Period 6: 12:45 - 1:40
        {"start": time(12, 45), "end": time(13, 40), "is_break": False},
    ]
    
    # Create time slots if they don't exist
    for slot in time_slots:
        existing = TimeSlot.query.filter_by(
            start_time=slot["start"], 
            end_time=slot["end"]
        ).first()
        
        if not existing:
            new_slot = TimeSlot()
            new_slot.start_time = slot["start"]
            new_slot.end_time = slot["end"]
            new_slot.is_break = slot["is_break"]
            db.session.add(new_slot)
    
    # Commit all changes
    db.session.commit()
