#!/usr/bin/env python

"""SIS sync script"""

import argparse
import logging
import logging.config
import os
import sys
from datetime import datetime

import yaml

import managers

log = logging.getLogger(__name__)


def main() -> int:
    """Main entrypoint"""

    args = get_args()
    configure_logging(args)
    
    log.info("beginning sync")

    # TODO: Add a portable pid file check back in
    try:
        sync(args)
        log.info("sync finished")
        return 0
    except Exception as exc:
        log.exception("Sync finished with error: %s", exc)
        return 1


def configure_logging(args):
    log_config_file = args.logging_config

    with open(log_config_file) as f_in:
        data = yaml.load(f_in, Loader=yaml.Loader)
        if None in data["loggers"]:
            data["loggers"][''] = data["loggers"][None]
            del data["loggers"][None]
        logging.config.dictConfig(data)

def sync(args):
    auth = (args.username, args.password)
    api_root = args.api_root

    academic_years = managers.AcademicYearManager(api_root, auth)
    grades = managers.GradeManager(api_root, auth)
    dorms = managers.DormManager(api_root, auth)
    detention_offenses = managers.DetentionOffenseManager(api_root, auth)
    detention_codes = managers.DetentionCodeManager(api_root, auth)

    parents = managers.ParentManager(
        api_root,
        auth=auth,
        ks_filename=args.families_file)

    parents.sync()

    students = managers.StudentManager(
        api_root,
        auth=auth,
        ks_filename=args.student_file)

    students.sync()

    teachers = managers.TeacherManager(
        api_root,
        auth=auth,
        ks_filename=args.teacher_file)

    teachers.sync()

    courses = managers.CourseManager(
        api_root,
        auth=auth,
        ks_filename=args.course_file)

    courses.sync()

    sections = managers.SectionManager(
        api_root,
        auth,
        ks_filename=args.section_file,
        academic_year_manager=academic_years,
        teacher_manager=teachers,
        course_manager=courses)

    sections.sync()

    student_registrations = managers.StudentRegistrationManager(
        api_root,
        auth=auth,
        ks_filename=args.student_registration_file,
        academic_year_manager=academic_years,
        section_manager=sections,
        student_manager=students)

    student_registrations.sync()

    enrollments = managers.EnrollmentManager(
        api_root,
        auth=auth,
        ks_filename=args.enrollments_file,
        academic_year_manager=academic_years,
        grade_manager=grades,
        student_manager=students,
        teacher_manager=teachers,
        dorm_manager=dorms)

    enrollments.sync()

    detentions = managers.DetentionManager(
        api_root,
        auth,
        ks_filename=args.detention_file,
        academic_year_manager=academic_years,
        offense_manager=detention_offenses,
        code_manager=detention_codes,
        student_manager=students,
        teacher_manager=teachers)

    detentions.sync()


def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--families-file",
                        default=os.environ.get("FAMILIES_FILE",
                                               "data/ptFAMILIES.xml.json"))

    parser.add_argument("--student-file",
                        default=os.environ.get("STUDENT_FILE",
                                               "data/ksPERMRECS.xml.json"))

    parser.add_argument("--teacher-file",
                        default=os.environ.get("TEACHER_FILE",
                                               "data/ksTEACHERS.xml.json"))

    parser.add_argument("--detention-file",
                        default=os.environ.get("DETENTION_FILE",
                                               "data/discipline.xml.json"))

    parser.add_argument("--course-file",
                        default=os.environ.get("COURSE_FILE",
                                               "data/ksCOURSES.xml.json"))

    parser.add_argument("--section-file",
                        default=os.environ.get("SECTION_FILE",
                                               "data/ksSECTIONS.xml.json"))

    parser.add_argument("--student-registration-file",
                        default=os.environ.get("STUDENT_REGISTRATION_FILE",
                                               "data/ksSTUDENTREG.xml.json"))

    parser.add_argument("--enrollments-file",
                        default=os.environ.get("ENROLLMENTS_FILE",
                                               "data/ksENROLLMENT.xml.json"))

    parser.add_argument("--api-root", default=os.environ.get("API_ROOT"))
    parser.add_argument("--username",  default=os.environ.get("USERNAME"))
    parser.add_argument("--password",  default=os.environ.get("PASSWORD"))
    
    parser.add_argument("--logging-config",
                        default=os.environ.get("LOGGING_CONFIG_FILE",
                                               "logging_default.yml"))

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    log.info("Sync process started")
    started_at = datetime.now()
    ret_code = main()
    delta = datetime.now() - started_at
    log.info("Sync process exiting with return code %d in %0.2f seconds", ret_code, delta.total_seconds(), extra={'return-code': ret_code, 'run-time': delta.total_seconds()})

    if ret_code != 0:
        # This is mainly to make the debugger happier
        sys.exit(ret_code)
    
