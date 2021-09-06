#!/usr/bin/env python

"""SIS sync script"""

import argparse
import logging
import os
import pidfile

from managers import AcademicYearManager, DetentionCodeManager, DetentionManager, DetentionOffenseManager, DormManager, EnrollmentManager, GradeManager, ParentManager, SectionManager, StudentManager, StudentRegistrationManager, TeacherManager, CourseManager

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)


def main():
    """Main entrypoint"""

    parser = argparse.ArgumentParser()

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

    parser.add_argument("--families-file",
                        default=os.environ.get("FAMILIES_FILE",
                                               "data/ptFAMILIES.xml.json"))

    parser.add_argument("--api-root", default=os.environ.get("API_ROOT"))
    parser.add_argument("--username",  default=os.environ.get("USERNAME"))
    parser.add_argument("--password",  default=os.environ.get("PASSWORD"))

    args = parser.parse_args()

    auth = (args.username, args.password)
    api_root = args.api_root

    with pidfile.PidFile('running.pid'):
        log.info("Pid lock acquired")

        academic_years = AcademicYearManager(api_root, auth)
        grades = GradeManager(api_root, auth)
        dorms = DormManager(api_root, auth)
        detention_offenses = DetentionOffenseManager(api_root, auth)
        detention_codes = DetentionCodeManager(api_root, auth)

        students = StudentManager(api_root,
                                  auth=auth,
                                  ks_filename=args.student_file)
        students.sync()

        teachers = TeacherManager(api_root,
                                  auth=auth,
                                  ks_filename=args.teacher_file)
        teachers.sync()

        courses = CourseManager(api_root,
                                auth=auth,
                                ks_filename=args.course_file)
        courses.sync()

        sections = SectionManager(api_root,
                                  auth,
                                  ks_filename=args.section_file,
                                  academic_year_manager=academic_years,
                                  teacher_manager=teachers,
                                  course_manager=courses)

        sections.sync()

        student_registrations = StudentRegistrationManager(api_root,
                                                           auth=auth,
                                                           ks_filename=args.student_registration_file,
                                                           academic_year_manager=academic_years,
                                                           section_manager=sections,
                                                           student_manager=students)
        student_registrations.sync()

        enrollments = EnrollmentManager(api_root,
                                        auth=auth,
                                        ks_filename=args.enrollments_file,
                                        academic_year_manager=academic_years,
                                        grade_manager=grades,
                                        student_manager=students,
                                        teacher_manager=teachers,
                                        dorm_manager=dorms,)
        enrollments.sync()

        parents = ParentManager(api_root, auth=auth,
                                ks_filename=args.families_file)
        parents.sync()

        detentions = DetentionManager(api_root,
                                      auth,
                                      ks_filename=args.detention_file,
                                      academic_year_manager=academic_years,
                                      offense_manager=detention_offenses,
                                      code_manager=detention_codes,
                                      student_manager=students,
                                      teacher_manager=teachers,)
        detentions.sync()


if __name__ == "__main__":
    main()
