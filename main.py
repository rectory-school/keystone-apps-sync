#!/usr/bin/env python

"""SIS sync script"""

import argparse
import logging
import os

from managers import ParentManager, StudentManager, TeacherManager, CourseManager

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)


def main():
    """Main entrypoint"""

    parser = argparse.ArgumentParser()
    parser.add_argument("--student-file", default=os.environ.get("STUDENT_FILE", "data/ksPERMRECS.xml.json"))
    parser.add_argument("--teacher-file", default=os.environ.get("TEACHER_FILE", "data/ksTEACHERS.xml.json"))
    parser.add_argument("--course-file", default=os.environ.get("COURSE_FILE", "data/ksCOURSES.xml.json"))
    parser.add_argument("--families-file", default=os.environ.get("FAMILIES_FILE", "data/ptFAMILIES.xml.json"))
    parser.add_argument("--api-root", default=os.environ.get("API_ROOT"))
    parser.add_argument("--username",  default=os.environ.get("USERNAME"))
    parser.add_argument("--password",  default=os.environ.get("PASSWORD"))

    args = parser.parse_args()
    auth = (args.username, args.password)

    students = StudentManager(args.api_root, auth=auth,
                              ks_filename=args.student_file)
    students.sync()

    teachers = TeacherManager(args.api_root, auth=auth,
                              ks_filename=args.teacher_file)
    teachers.sync()

    courses = CourseManager(args.api_root, auth=auth,
                            ks_filename=args.course_file)
    courses.sync()

    parents = ParentManager(args.api_root, auth=auth,
                            ks_filename=args.families_file)
    parents.sync()


if __name__ == "__main__":
    main()
