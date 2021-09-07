"""Student reconciler"""

import logging

from typing import Dict, Iterable, Any, Hashable, Tuple, Optional
from manager import AppsManager, SyncManager, GetOrCreateManager, MissingKeyValue, MissingKey
from parsers import active_parse, email_parse_continue_blank, is_boarder_from_boarder_day

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

    subvalue_map = {
        'first_name': 'first',
        'last_name': 'last',
        'email': 'email',
        'phone_work': 'phone_W',
        'phone_cell': 'phone_cell',
        'middle_name': 'middle',
        'full_name': 'full',
    }

    def split(self, ks_record: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
        did_create = False

        for prefix in ('Pa', 'Pb'):
            out = {}

            for apps_attr, ks_attr in self.subvalue_map.items():
                value = ks_record[prefix + "_" + ks_attr].strip()
                if value:
                    out[apps_attr] = value

            # We had at least one value in this parent
            if out:
                out['family_id'] = ks_record['IDFAMILY']
                out['address'] = ks_record['P_address_full'].strip()
                out['phone_home'] = ks_record["P_phone_H"].strip()
                out['parent_id'] = prefix

                if 'email' in out:
                    out['email'] = email_parse_continue_blank(
                        out['email'].strip())

                yield out

        if not did_create:
            # Create a synthetic Pa record

            yield {
                'family_id': ks_record['IDFAMILY'],
                'parent_id': 'Pa',
                'address': ks_record['P_address_full'].strip(),
                'phone_home': ks_record["P_phone_H"].strip(),
            }

    def get_key_value(self, record: Dict[str, Any]) -> Hashable:
        return (record["family_id"], record["parent_id"])


class AcademicYearManager(GetOrCreateManager):
    """Academic year manager"""

    url_key = 'academic_years'
    key_name = 'year'


class GradeManager(GetOrCreateManager):
    """Grade manager"""

    url_key = 'grades'
    key_name = 'grade'


class DormManager(GetOrCreateManager):
    """Dorm manager"""

    url_key = 'dorms'
    key_name = 'dorm_name'


class EnrollmentManager(SyncManager):
    url_key = "enrollments"

    field_map = [
        ('student', 'IDStudent'),
        ('academic_year', 'AcademicYear'),
        ('boarder', 'BoarderDay'),
        ('dorm', 'DormName'),
        ('grade', 'Grade'),
        ('division', 'Division'),
        ('section', 'Section Letter'),
        ('advisor', 'IDAdvisor'),
        ('status_enrollment', 'StatusEnrollment'),
        ('status_attending', 'StatusAttending'),
        ('enrolled_date', 'EnrollmentDate')
    ]

    def __init__(self,
                 api_root: str,
                 auth: Tuple[str, str],
                 ks_filename: str,
                 academic_year_manager: AcademicYearManager,
                 grade_manager: GradeManager,
                 student_manager: StudentManager,
                 teacher_manager: TeacherManager,
                 dorm_manager: DormManager):

        super().__init__(api_root, auth, ks_filename=ks_filename)

        self.field_translations = {
            'grade': grade_manager.get_url_for_key,
            'academic_year': academic_year_manager.get_url_for_key,
            'student': student_manager.get_url_for_key,
            'advisor': teacher_manager.get_url_for_key,
            'boarder': is_boarder_from_boarder_day,
            'dorm': dorm_manager.get_url_for_key,
        }

    def get_key_value(self, record: Dict[str, Any]) -> Hashable:
        return (record['student'], record['academic_year'])


class SectionManager(SyncManager):
    """Section manager"""

    url_key = 'sections'
    field_map = [
        ('academic_year', 'AcademicYear'),
        ('course', 'CourseNumber'),
        ('csn', 'CourseSectionNumber'),
        ('teacher', 'IDTeacher')
    ]

    required_fields = ['course', 'csn', 'academic_year']

    def __init__(self, api_root: str,
                 auth: Tuple[str, str],
                 ks_filename: str,
                 academic_year_manager: AcademicYearManager,
                 teacher_manager: TeacherManager,
                 course_manager: CourseManager):

        super().__init__(api_root, auth, ks_filename=ks_filename)

        self.field_translations = {
            'teacher': teacher_manager.get_url_for_key,
            'course': course_manager.get_url_for_key,
            'academic_year': academic_year_manager.get_url_for_key,
        }

    def get_key_value(self, record: Dict[str, Any]) -> Hashable:
        return (record['academic_year'], record['csn'])


class DetentionCodeManager(GetOrCreateManager):
    """Get only """

    url_key = 'detention_codes'
    key_name = 'code'


class DetentionOffenseManager(GetOrCreateManager):
    """Get only """

    url_key = 'detention_offenses'
    key_name = 'offense'


class DetentionManager(SyncManager):
    url_key = 'detentions'
    key_name = 'detention_id'

    field_map = [
        ('detention_id', 'IDINCIDENT'),
        ('academic_year', 'AcademicYear'),
        ('comments', 'Comments'),
        ('date', 'Det Date'),
        ('offense', 'Offense'),
        ('student', 'IDSTUDENT'),
        ('teacher', 'KSTeachers::IDTEACHER'),
        ('code', 'Code'),
    ]

    required_fields = ['offense', 'student', 'academic_year', 'teacher']

    def __init__(self, api_root: str,
                 auth: Tuple[str, str],
                 ks_filename: str,
                 academic_year_manager: AcademicYearManager,
                 student_manager: StudentManager,
                 teacher_manager: TeacherManager,
                 offense_manager: DetentionOffenseManager,
                 code_manager: DetentionCodeManager):

        super().__init__(api_root, auth, ks_filename=ks_filename)

        self.field_translations = {
            'academic_year': academic_year_manager.get_url_for_key,
            'student': student_manager.get_url_for_key,
            'teacher': teacher_manager.get_url_for_key,
            'offense': offense_manager.get_url_for_key,
            'code': code_manager.get_url_for_key,
        }


class StudentRegistrationManager(SyncManager):
    """Student registration manager"""

    url_key = 'student_registrations'
    key_name = 'student_reg_id'

    def __init__(self, api_root: str,
                 auth: Tuple[str, str],
                 ks_filename: str,
                 academic_year_manager: AcademicYearManager,
                 section_manager: SectionManager,
                 student_manager: StudentManager,
                 ):
        super().__init__(api_root, auth, ks_filename=ks_filename)

        self.academic_year_manager = academic_year_manager
        self.section_manager = section_manager
        self.student_manager = student_manager

    def translate(self, ks_record: Dict[str, Any]) -> Dict[str, Any]:
        """Overriding translate to get a multi-get section out of academic year and CSN"""

        if not 'IDSTUDENTREG' in ks_record:
            raise MissingKey(ks_record)

        if not ks_record['IDSTUDENTREG']:
            raise MissingKeyValue(ks_record)

        section_lookup_record = {
            'academic_year': self.academic_year_manager.get_url_for_key(ks_record['AcademicYear']),
            'csn': ks_record['CSN']
        }

        section_key = self.section_manager.get_key_value(section_lookup_record)

        section = self.section_manager.get_url_for_key(section_key)
        out = {
            'student_reg_id': ks_record['IDSTUDENTREG'],
            'student': self.student_manager.get_url_for_key(ks_record['IDStudent']),
            'section': section,
        }

        if not out['student']:
            raise MissingKeyValue(ks_record)
        
        if not out['section']:
            raise MissingKeyValue(ks_record)

        return out
