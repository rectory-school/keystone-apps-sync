"""Student reconciler"""

import logging

from manager import SyncManager
from parsers import active_parse, email_parse_continue_blank

log = logging.getLogger(__name__)


class StudentManager(SyncManager):
    url_key = 'students'
    key_name = 'student_id'

    field_map = [
        ('student_id', 'IDSTUDENT'),
        ('first_name', 'NameFirst'),
        ('last_name', 'NameLast'),
        ('nickname', 'NameNickname'),
        ('email', 'EMailSchool'),
        ('gender', 'Sex'),
    ]

    field_translations = {
        'email': email_parse_continue_blank,
    }


class TeacherManager(SyncManager):
    url_key = 'teachers'
    key_name = 'teacher_id'

    field_map = [
        ('teacher_id', 'IDTEACHER'),
        ('unique_name', 'NameUnique'),
        ('first_name', 'NameFirst'),
        ('last_name', 'NameLast'),
        ('prefix', 'NamePrefix'),
        ('email', 'EmailSchool'),
        ('active', 'Active Employee'),
    ]

    field_translations = {
        'active': active_parse,
    }


class CourseManager(SyncManager):
    url_key = 'courses'
    key_name = 'number'

    field_map = [
        ('number', 'CourseNumber'),
        ('course_name', 'CourseName'),
        ('course_name_short', 'CourseNameShort'),
        ('course_name_transcript', 'CourseNameTranscript'),
        ('division', 'Division'),
        ('grade_level', 'GradeLevel'),
        ('department', 'DepartmentName'),
        ('course_type', 'CourseType'),
    ]

class ParentManager(SyncManager):
    url_key = 'parents'
