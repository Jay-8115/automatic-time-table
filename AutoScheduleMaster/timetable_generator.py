from app import db
from models import Class, Section, Teacher, Course, CourseAssignment, TimeSlot, Day, TimetableEntry
import random
from datetime import time
import logging

def generate_timetable(class_id):
    """
    Generate a timetable for all sections of a class based on available courses, teachers, and constraints.
    
    Args:
        class_id: ID of the class to generate timetable for
        
    Returns:
        (success, message): Tuple with success boolean and message string
    """
    try:
        # Get all necessary data
        class_obj = Class.query.get(class_id)
        if not class_obj:
            return False, "Class not found"
            
        sections = Section.query.filter_by(class_id=class_id).all()
        if not sections:
            return False, "No sections found for this class"
            
        # Get course assignments for this class
        assignments = CourseAssignment.query.filter_by(class_id=class_id).all()
        if not assignments:
            return False, "No courses assigned to this class"
            
        days = Day.query.order_by(Day.id).all()
        if not days:
            return False, "No days defined in the system"
            
        # Get all time slots, excluding breaks
        time_slots = TimeSlot.query.filter_by(is_break=False).order_by(TimeSlot.start_time).all()
        breaks = TimeSlot.query.filter_by(is_break=True).all()
        
        # Create a dictionary to track teacher schedules across all sections
        teacher_schedule = {}  # {teacher_id: {day_id: {time_slot_id: True}}}
        for assignment in assignments:
            if assignment.teacher_id not in teacher_schedule:
                teacher_schedule[assignment.teacher_id] = {day.id: {} for day in days}
                
        # Create lists for lecture and lab assignments
        lecture_assignments = []
        lab_assignments = []
        
        for assignment in assignments:
            course = Course.query.get(assignment.course_id)
            teacher = Teacher.query.get(assignment.teacher_id)
            
            if not course or not teacher:
                continue
                
            # Only include lab type if course has lab enabled
            if course.is_lab and course.lab_hours > 0:
                lab_assignments.append({
                    'course_id': course.id,
                    'teacher_id': teacher.id,
                    'is_lab': True,
                    'hours': course.lab_hours
                })
            
            # Only include lecture type if course has lecture enabled
            if course.is_lecture and course.lecture_hours > 0:
                lecture_assignments.append({
                    'course_id': course.id,
                    'teacher_id': teacher.id,
                    'is_lab': False,
                    'hours': course.lecture_hours
                })
        
        # First, delete any existing timetable entries to avoid unique constraint violations
        existing_entries = []
        for section in sections:
            section_entries = TimetableEntry.query.filter_by(section_id=section.id).all()
            existing_entries.extend(section_entries)
        
        for entry in existing_entries:
            db.session.delete(entry)
        
        db.session.commit()
        
        # Create a class-wide schedule to track all occupied slots
        class_schedule = {day.id: {} for day in days}
        
        # Track section-specific schedules
        section_schedules = {}
        for section in sections:
            section_schedules[section.id] = {day.id: {} for day in days}
        
        # Randomize the assignments for better distribution
        random.shuffle(lab_assignments)
        random.shuffle(lecture_assignments)
            
        # First, group lab assignments by course
        labs_by_course = {}
        for lab_assignment in lab_assignments:
            course_id = lab_assignment['course_id']
            if course_id not in labs_by_course:
                labs_by_course[course_id] = []
            labs_by_course[course_id].append(lab_assignment)
        
        # Schedule labs - same time for all sections, but different teacher assignments
        for course_id, course_assignments in labs_by_course.items():
            course = Course.query.get(course_id)
            if not course or not course.is_lab:
                continue
                
            # Get first assignment to determine hours needed
            if not course_assignments:
                continue
                
            sample_assignment = course_assignments[0]
            remaining_hours = sample_assignment['hours']
            
            # Each lab session requires two consecutive periods
            while remaining_hours > 0:
                # Find a suitable day and time slot for the lab
                placed = False
                for day in days:
                    # We need to find two consecutive non-break periods for labs
                    for i in range(len(time_slots) - 1):
                        # Check if these are consecutive time slots without a break in between
                        if time_slots[i].end_time != time_slots[i+1].start_time:
                            continue
                            
                        # Check if both time slots are available in the class schedule
                        slot1_free = (day.id not in class_schedule or 
                                     time_slots[i].id not in class_schedule[day.id])
                        slot2_free = (day.id not in class_schedule or 
                                     time_slots[i+1].id not in class_schedule[day.id])
                        
                        # Check teacher availability for all teachers in this course
                        teachers_available = True
                        for assignment in course_assignments:
                            teacher_id = assignment['teacher_id']
                            slot1_free_for_teacher = (time_slots[i].id not in 
                                                     teacher_schedule[teacher_id][day.id])
                            slot2_free_for_teacher = (time_slots[i+1].id not in 
                                                     teacher_schedule[teacher_id][day.id])
                            
                            if not (slot1_free_for_teacher and slot2_free_for_teacher):
                                teachers_available = False
                                break
                        
                        if slot1_free and slot2_free and teachers_available:
                            # Found a suitable slot for labs - allocate different teachers to different sections
                            # but at the same time
                            
                            # Update class schedule first - block this time for all sections
                            if day.id not in class_schedule:
                                class_schedule[day.id] = {}
                            class_schedule[day.id][time_slots[i].id] = True
                            class_schedule[day.id][time_slots[i+1].id] = True
                            
                            # Assign different lab teachers to different sections
                            section_index = 0
                            for section in sections:
                                # Get the teacher assignment (rotate if needed)
                                assignment = course_assignments[section_index % len(course_assignments)]
                                section_index += 1
                                
                                teacher_id = assignment['teacher_id']
                                
                                # Update teacher schedule
                                teacher_schedule[teacher_id][day.id][time_slots[i].id] = True
                                teacher_schedule[teacher_id][day.id][time_slots[i+1].id] = True
                                
                                # Update section schedule
                                if day.id not in section_schedules[section.id]:
                                    section_schedules[section.id][day.id] = {}
                                section_schedules[section.id][day.id][time_slots[i].id] = True
                                section_schedules[section.id][day.id][time_slots[i+1].id] = True
                                
                                # First slot
                                entry1 = TimetableEntry()
                                entry1.section_id = section.id
                                entry1.day_id = day.id
                                entry1.time_slot_id = time_slots[i].id
                                entry1.course_id = course_id
                                entry1.teacher_id = teacher_id
                                db.session.add(entry1)
                                
                                # Second slot
                                entry2 = TimetableEntry()
                                entry2.section_id = section.id
                                entry2.day_id = day.id
                                entry2.time_slot_id = time_slots[i+1].id
                                entry2.course_id = course_id
                                entry2.teacher_id = teacher_id
                                db.session.add(entry2)
                            
                            db.session.commit()
                            placed = True
                            remaining_hours -= 1  # Count as 1 lab session placed
                            break
                    
                    if placed:
                        break
                
                # If we couldn't place the lab or no more hours, move on
                if not placed or remaining_hours <= 0:
                    break
            
            if remaining_hours > 0:
                # Could not place all lab hours
                logging.warning(f"Could not place all lab sessions for course {course_id} for class {class_id}")
        
        # Group lecture assignments by course
        lectures_by_course = {}
        for lecture_assignment in lecture_assignments:
            course_id = lecture_assignment['course_id']
            if course_id not in lectures_by_course:
                lectures_by_course[course_id] = []
            lectures_by_course[course_id].append(lecture_assignment)
        
        # Schedule lectures - same for all sections with the same teacher
        for course_id, course_assignments in lectures_by_course.items():
            course = Course.query.get(course_id)
            if not course or not course.is_lecture:
                continue
                
            # Get first assignment to determine hours needed
            if not course_assignments:
                continue
                
            # Use the first teacher assignment for this course for all sections
            # This ensures lectures are identical across sections
            main_assignment = course_assignments[0]
            teacher_id = main_assignment['teacher_id']
            remaining_hours = main_assignment['hours']
            
            while remaining_hours > 0:
                placed = False
                for attempt in range(10):  # Try harder to place lectures
                    day = random.choice(days)
                    time_slot = random.choice(time_slots)
                    
                    # Skip break slots
                    if time_slot.is_break:
                        continue
                    
                    # Check if this slot is free in the class schedule
                    slot_free = (day.id not in class_schedule or 
                                time_slot.id not in class_schedule[day.id])
                    
                    # Check teacher availability
                    teacher_slot_free = (time_slot.id not in 
                                        teacher_schedule[teacher_id][day.id])
                    
                    if slot_free and teacher_slot_free:
                        # Update class schedule
                        if day.id not in class_schedule:
                            class_schedule[day.id] = {}
                        class_schedule[day.id][time_slot.id] = True
                        
                        # Update teacher schedule
                        teacher_schedule[teacher_id][day.id][time_slot.id] = True
                        
                        # Add the lecture to all sections at the same time with the same teacher
                        for section in sections:
                            # Update section schedule
                            if day.id not in section_schedules[section.id]:
                                section_schedules[section.id][day.id] = {}
                            section_schedules[section.id][day.id][time_slot.id] = True
                            
                            # Add the timetable entry
                            entry = TimetableEntry()
                            entry.section_id = section.id
                            entry.day_id = day.id
                            entry.time_slot_id = time_slot.id
                            entry.course_id = course_id
                            entry.teacher_id = teacher_id  # Use the same teacher for all sections
                            db.session.add(entry)
                        
                        db.session.commit()
                        remaining_hours -= 1
                        placed = True
                        break
                
                # If we couldn't place it after multiple attempts or no more hours, move on
                if not placed or remaining_hours <= 0:
                    break
            
            if remaining_hours > 0:
                logging.warning(f"Could not place all lecture sessions for course {course_id} for class {class_id}")
        
        # Add entries for breaks
        for day in days:
            for break_slot in breaks:
                for section in sections:
                    # Check if entry already exists
                    existing = TimetableEntry.query.filter_by(
                        section_id=section.id,
                        day_id=day.id,
                        time_slot_id=break_slot.id
                    ).first()
                    
                    if not existing:
                        entry = TimetableEntry()
                        entry.section_id = section.id
                        entry.day_id = day.id
                        entry.time_slot_id = break_slot.id
                        entry.course_id = None
                        entry.teacher_id = None
                        db.session.add(entry)
        
        # Commit any remaining changes
        db.session.commit()
        return True, "Timetable generated successfully"
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error generating timetable: {str(e)}")
        return False, f"Error: {str(e)}"
