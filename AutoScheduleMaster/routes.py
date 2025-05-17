from flask import render_template, redirect, url_for, request, flash, jsonify
from app import db
from models import User, Class, Section, Teacher, Course, CourseAssignment, TimeSlot, Day, TimetableEntry, init_default_data
from forms import ClassForm, SectionForm, TeacherForm, CourseForm, CourseAssignmentForm, LoginForm, RegistrationForm
from timetable_generator import generate_timetable
from datetime import datetime
from flask_login import login_user, logout_user, current_user, login_required

def register_routes(app):
    # Initialize default data (days and time slots)
    # Using app.before_request instead of before_first_request (deprecated)
    def setup_defaults():
        init_default_data(db)
    
    # Register the setup_defaults function to run when the app starts
    with app.app_context():
        setup_defaults()

    # Authentication routes
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                next_page = request.args.get('next')
                flash(f'Welcome back, {user.username}!', 'success')
                return redirect(next_page if next_page else url_for('index'))
            else:
                flash('Login failed. Please check your username and password.', 'danger')
        
        now = datetime.now()
        return render_template('login.html', form=form, now=now)
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
            
        form = RegistrationForm()
        if form.validate_on_submit():
            user = User()
            user.username = form.username.data
            user.email = form.email.data
            user.set_password(form.password.data)
            
            # Make the first user an admin
            if User.query.count() == 0:
                user.is_admin = True
                
            db.session.add(user)
            db.session.commit()
            
            flash('Your account has been created! You can now log in.', 'success')
            return redirect(url_for('login'))
            
        now = datetime.now()
        return render_template('register.html', form=form, now=now)
    
    @app.route('/logout')
    def logout():
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    @app.route('/')
    def index():
        # Count of various entities for dashboard
        class_count = Class.query.count()
        teacher_count = Teacher.query.count()
        course_count = Course.query.count()
        section_count = Section.query.count()
        
        # Add current date for the footer
        now = datetime.now()
        
        return render_template('index.html', 
                              class_count=class_count,
                              teacher_count=teacher_count,
                              course_count=course_count,
                              section_count=section_count,
                              now=now)

    # Class routes
    @app.route('/classes', methods=['GET', 'POST'])
    @login_required
    def classes():
        form = ClassForm()
        if form.validate_on_submit():
            new_class = Class()
            new_class.name = form.name.data
            db.session.add(new_class)
            db.session.commit()
            flash(f'Class {form.name.data} added successfully!', 'success')
            return redirect(url_for('classes'))
        
        classes = Class.query.all()
        now = datetime.now()
        return render_template('classes.html', classes=classes, form=form, now=now)

    @app.route('/classes/<int:class_id>/delete', methods=['POST'])
    @login_required
    def delete_class(class_id):
        class_obj = Class.query.get_or_404(class_id)
        db.session.delete(class_obj)
        db.session.commit()
        flash(f'Class {class_obj.name} deleted successfully!', 'success')
        return redirect(url_for('classes'))

    @app.route('/classes/<int:class_id>/sections', methods=['GET', 'POST'])
    @login_required
    def sections(class_id):
        class_obj = Class.query.get_or_404(class_id)
        form = SectionForm()
        
        if form.validate_on_submit():
            # Check if section already exists for this class
            existing = Section.query.filter_by(name=form.name.data, class_id=class_id).first()
            if existing:
                flash(f'Section {form.name.data} already exists for {class_obj.name}!', 'danger')
            else:
                new_section = Section()
                new_section.name = form.name.data
                new_section.class_id = class_id
                db.session.add(new_section)
                db.session.commit()
                flash(f'Section {form.name.data} added to {class_obj.name}!', 'success')
            return redirect(url_for('sections', class_id=class_id))
        
        sections = Section.query.filter_by(class_id=class_id).all()
        now = datetime.now()
        return render_template('classes.html', 
                              class_obj=class_obj, 
                              sections=sections, 
                              form=form,
                              section_view=True,
                              now=now)

    @app.route('/sections/<int:section_id>/delete', methods=['POST'])
    @login_required
    def delete_section(section_id):
        section = Section.query.get_or_404(section_id)
        class_id = section.class_id
        db.session.delete(section)
        db.session.commit()
        flash(f'Section {section.name} deleted successfully!', 'success')
        return redirect(url_for('sections', class_id=class_id))

    # Teacher routes
    @app.route('/teachers', methods=['GET', 'POST'])
    @login_required
    def teachers():
        form = TeacherForm()
        if form.validate_on_submit():
            new_teacher = Teacher()
            new_teacher.name = form.name.data
            new_teacher.email = form.email.data
            new_teacher.department = form.department.data
            
            db.session.add(new_teacher)
            db.session.commit()
            flash(f'Teacher {form.name.data} added successfully!', 'success')
            return redirect(url_for('teachers'))
        
        teachers = Teacher.query.all()
        now = datetime.now()
        return render_template('teachers.html', teachers=teachers, form=form, now=now)

    @app.route('/teachers/<int:teacher_id>/delete', methods=['POST'])
    @login_required
    def delete_teacher(teacher_id):
        teacher = Teacher.query.get_or_404(teacher_id)
        db.session.delete(teacher)
        db.session.commit()
        flash(f'Teacher {teacher.name} deleted successfully!', 'success')
        return redirect(url_for('teachers'))

    # Course routes
    @app.route('/courses', methods=['GET', 'POST'])
    @login_required
    def courses():
        form = CourseForm()
        if form.validate_on_submit():
            new_course = Course()
            new_course.name = form.name.data
            new_course.code = form.code.data
            new_course.is_lab = form.is_lab.data
            new_course.is_lecture = form.is_lecture.data
            
            # Convert hours to integers, defaulting to 0 if empty
            try:
                new_course.lab_hours = int(form.lab_hours.data) if form.lab_hours.data else 0
            except ValueError:
                new_course.lab_hours = 0
                
            try:
                new_course.lecture_hours = int(form.lecture_hours.data) if form.lecture_hours.data else 0
            except ValueError:
                new_course.lecture_hours = 0
            
            # Ensure at least one type is selected
            if not (new_course.is_lab or new_course.is_lecture):
                flash('Please select at least one course type (Lab or Lecture)', 'danger')
                courses = Course.query.all()
                now = datetime.now()
                return render_template('courses.html', courses=courses, form=form, now=now)
            
            db.session.add(new_course)
            db.session.commit()
            flash(f'Course {form.name.data} added successfully!', 'success')
            return redirect(url_for('courses'))
        
        courses = Course.query.all()
        now = datetime.now()
        return render_template('courses.html', courses=courses, form=form, now=now)

    @app.route('/courses/<int:course_id>/delete', methods=['POST'])
    @login_required
    def delete_course(course_id):
        course = Course.query.get_or_404(course_id)
        db.session.delete(course)
        db.session.commit()
        flash(f'Course {course.name} deleted successfully!', 'success')
        return redirect(url_for('courses'))

    # Course Assignment routes
    @app.route('/assign-courses', methods=['GET', 'POST'])
    @login_required
    def assign_courses():
        form = CourseAssignmentForm()
        # Populate form choices
        form.class_id.choices = [(c.id, c.name) for c in Class.query.all()]
        form.teacher_id.choices = [(t.id, t.name) for t in Teacher.query.all()]
        form.course_id.choices = [(c.id, f"{c.name} ({c.code})") for c in Course.query.all()]
        
        if form.validate_on_submit():
            course = Course.query.get(form.course_id.data)
            if not course:
                flash('Selected course not found!', 'danger')
                return redirect(url_for('assign_courses'))
            
            # Assign lecture type if course has lecture enabled
            if course.is_lecture:
                existing_lecture = CourseAssignment.query.filter_by(
                    class_id=form.class_id.data,
                    teacher_id=form.teacher_id.data,
                    course_id=form.course_id.data
                ).first()
                if not existing_lecture:
                    new_lecture_assignment = CourseAssignment()
                    new_lecture_assignment.class_id = form.class_id.data
                    new_lecture_assignment.teacher_id = form.teacher_id.data
                    new_lecture_assignment.course_id = form.course_id.data
                    db.session.add(new_lecture_assignment)
            
            # Assign lab type if course has lab enabled
            if course.is_lab:
                # For lab, we might want to assign different teachers or handle differently
                # But since CourseAssignment links course to teacher and class, 
                # we add the same assignment if not exists
                existing_lab = CourseAssignment.query.filter_by(
                    class_id=form.class_id.data,
                    teacher_id=form.teacher_id.data,
                    course_id=form.course_id.data
                ).first()
                if not existing_lab:
                    new_lab_assignment = CourseAssignment()
                    new_lab_assignment.class_id = form.class_id.data
                    new_lab_assignment.teacher_id = form.teacher_id.data
                    new_lab_assignment.course_id = form.course_id.data
                    db.session.add(new_lab_assignment)
            
            db.session.commit()
            flash('Course assignment(s) added successfully!', 'success')
            return redirect(url_for('assign_courses'))
        
        # Get all existing assignments
        assignments = db.session.query(
            CourseAssignment, Class, Teacher, Course
        ).join(
            Class, CourseAssignment.class_id == Class.id
        ).join(
            Teacher, CourseAssignment.teacher_id == Teacher.id
        ).join(
            Course, CourseAssignment.course_id == Course.id
        ).all()
        
        now = datetime.now()
        return render_template('courses.html', 
                              form=form, 
                              assignments=assignments,
                              assignment_view=True,
                              now=now)

    @app.route('/assignments/<int:assignment_id>/delete', methods=['POST'])
    @login_required
    def delete_assignment(assignment_id):
        assignment = CourseAssignment.query.get_or_404(assignment_id)
        db.session.delete(assignment)
        db.session.commit()
        flash('Course assignment deleted successfully!', 'success')
        return redirect(url_for('assign_courses'))

    # Timetable generation routes
    @app.route('/timetable', methods=['GET'])
    @login_required
    def timetable():
        classes = Class.query.all()
        now = datetime.now()
        return render_template('timetable.html', classes=classes, now=now)

    @app.route('/generate-timetable/<int:class_id>', methods=['POST'])
    @login_required
    def generate_timetable_for_class(class_id):
        # Clear existing timetable entries for this class
        class_obj = Class.query.get_or_404(class_id)
        sections = Section.query.filter_by(class_id=class_id).all()
        
        if not sections:
            flash(f'No sections found for {class_obj.name}. Add sections first.', 'danger')
            return redirect(url_for('timetable'))
        
        section_ids = [section.id for section in sections]
        existing_entries = TimetableEntry.query.filter(TimetableEntry.section_id.in_(section_ids)).all()
        
        for entry in existing_entries:
            db.session.delete(entry)
        db.session.commit()
        
        # Generate the timetable
        success, message = generate_timetable(class_id)
        
        if success:
            flash(f'Timetable for {class_obj.name} generated successfully!', 'success')
        else:
            flash(f'Failed to generate timetable: {message}', 'danger')
        
        return redirect(url_for('view_timetable', class_id=class_id))

    @app.route('/view-timetable/<int:class_id>', methods=['GET'])
    @login_required
    def view_timetable(class_id):
        class_obj = Class.query.get_or_404(class_id)
        sections = Section.query.filter_by(class_id=class_id).all()
        days = Day.query.order_by(Day.id).all()
        time_slots = TimeSlot.query.order_by(TimeSlot.start_time).all()
        
        # Build the timetable data for each section
        section_timetables = {}
        
        for section in sections:
            timetable_data = {}
            
            for day in days:
                timetable_data[day.id] = {}
                
                for slot in time_slots:
                    # Find the timetable entry for this day and time slot
                    entry = TimetableEntry.query.filter_by(
                        section_id=section.id,
                        day_id=day.id,
                        time_slot_id=slot.id
                    ).first()
                    
                    if entry and entry.course:
                        timetable_data[day.id][slot.id] = {
                            'course': entry.course.name,
                            'course_code': entry.course.code,
                            'teacher': entry.teacher.name if entry.teacher else 'N/A',
                            'is_lab': entry.course.is_lab,
                            'is_lecture': entry.course.is_lecture
                        }
                    else:
                        timetable_data[day.id][slot.id] = None
            
            section_timetables[section.id] = timetable_data
        
        # Create a consolidated class timetable that shows both the common lectures and the section-specific labs
        consolidated_timetable = {}
        
        # Initialize the consolidated timetable structure
        for day in days:
            consolidated_timetable[day.id] = {}
            for slot in time_slots:
                consolidated_timetable[day.id][slot.id] = {
                    'common': None,  # For lectures and other common entries
                    'sections': {}   # For section-specific entries like labs
                }
                
                # Check if there's a common entry for all sections at this time slot
                is_common_entry = True
                reference_entry = None
                
                # Find entries for all sections at this time slot
                for section in sections:
                    entry = TimetableEntry.query.filter_by(
                        section_id=section.id,
                        day_id=day.id,
                        time_slot_id=slot.id
                    ).first()
                    
                    if not entry or not entry.course:
                        is_common_entry = False
                        break
                    
                    if not reference_entry:
                        reference_entry = entry
                    elif (entry.course_id != reference_entry.course_id or 
                          entry.teacher_id != reference_entry.teacher_id):
                        is_common_entry = False
                        
                # If it's a common entry (like lecture), store it in the common field
                if is_common_entry and reference_entry and reference_entry.course.is_lecture:
                    consolidated_timetable[day.id][slot.id]['common'] = {
                        'course': reference_entry.course.name,
                        'course_code': reference_entry.course.code,
                        'teacher': reference_entry.teacher.name if reference_entry.teacher else 'N/A',
                        'is_lecture': True
                    }
                else:
                    # Store section-specific entries (like labs) in the sections field
                    for section in sections:
                        entry = TimetableEntry.query.filter_by(
                            section_id=section.id,
                            day_id=day.id,
                            time_slot_id=slot.id
                        ).first()
                        
                        if entry and entry.course and entry.course.is_lab:
                            consolidated_timetable[day.id][slot.id]['sections'][section.id] = {
                                'course': entry.course.name,
                                'course_code': entry.course.code,
                                'teacher': entry.teacher.name if entry.teacher else 'N/A',
                                'is_lab': True
                            }
                        
        now = datetime.now()    
        return render_template('timetable_view.html',
                              class_obj=class_obj,
                              sections=sections,
                              days=days,
                              time_slots=time_slots,
                              section_timetables=section_timetables,
                              consolidated_timetable=consolidated_timetable,
                              now=now)

    @app.route('/api/timetable/<int:class_id>', methods=['GET'])
    def api_timetable(class_id):
        """API endpoint to get timetable data for a class in JSON format"""
        class_obj = Class.query.get_or_404(class_id)
        sections = Section.query.filter_by(class_id=class_id).all()
        days = Day.query.order_by(Day.id).all()
        time_slots = TimeSlot.query.order_by(TimeSlot.start_time).all()
        
        # Build the response data
        response = {
            'class': {
                'id': class_obj.id,
                'name': class_obj.name
            },
            'sections': [],
            'days': [{'id': day.id, 'name': day.name} for day in days],
            'time_slots': [{
                'id': slot.id, 
                'start': slot.start_time.strftime('%H:%M'), 
                'end': slot.end_time.strftime('%H:%M'),
                'is_break': slot.is_break
            } for slot in time_slots]
        }
        
        for section in sections:
            section_data = {
                'id': section.id,
                'name': section.name,
                'timetable': {}
            }
            
            for day in days:
                section_data['timetable'][day.id] = {}
                
                for slot in time_slots:
                    entry = TimetableEntry.query.filter_by(
                        section_id=section.id,
                        day_id=day.id,
                        time_slot_id=slot.id
                    ).first()
                    
                    if entry and entry.course:
                        section_data['timetable'][day.id][slot.id] = {
                            'course_id': entry.course_id,
                            'course_name': entry.course.name,
                            'course_code': entry.course.code,
                            'teacher_id': entry.teacher_id,
                            'teacher_name': entry.teacher.name if entry.teacher else None,
                            'is_lab': entry.course.is_lab
                        }
                    else:
                        section_data['timetable'][day.id][slot.id] = None
            
            response['sections'].append(section_data)
        
        return jsonify(response)

    return app
