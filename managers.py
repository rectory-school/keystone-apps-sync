"""Student reconciler"""

import logging

from typing import Dict, Iterable, Any, Hashable
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
                value = ks_record[prefix + "_" + ks_attr]
                if value:
                    out[apps_attr] = value

            # We had at least one value in this parent
            if out:
                out['family_id'] = ks_record['IDFAMILY']
                out['address'] = ks_record['P_address_full']
                out['phone_home'] = ks_record["P_phone_H"]
                out['parent_id'] = prefix

                if 'email' in out:
                    out['email'] = email_parse_continue_blank(out['email'].strip())

                yield out

        if not did_create:
            # Create a synthetic Pa record

            yield {
                'family_id': ks_record['IDFAMILY'],
                'parent_id': 'Pa',
                'address': ks_record['P_address_full'],
                'phone_home': ks_record["P_phone_H"],
            }
    
    def get_key_value(self, record: Dict[str, Any]) -> Hashable:
        return (record["family_id"], record["parent_id"])
