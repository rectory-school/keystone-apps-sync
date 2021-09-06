#!/usr/bin/env python

"""SIS sync script"""

import argparse
import logging

from managers import StudentManager, TeacherManager, CourseManager

logging.basicConfig(level=logging.INFO)

log = logging.getLogger(__name__)


def main():
    """Main entrypoint"""

    parser = argparse.ArgumentParser()
    parser.add_argument("--student-file", default="ksPERMRECS.xml.json")
    parser.add_argument("--teacher-file", default="ksTEACHERS.xml.json")
    parser.add_argument("--course-file", default="ksCOURSES.xml.json")
    parser.add_argument("--api-root", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)

    args = parser.parse_args()
    auth = (args.username, args.password)

    students = StudentManager(args.api_root, auth=auth, ks_filename=args.student_file)
    students.sync()

    teachers = TeacherManager(args.api_root, auth=auth, ks_filename=args.teacher_file)
    teachers.sync()

    courses = CourseManager(args.api_root, auth=auth, ks_filename=args.course_file)
    courses.sync()


if __name__ == "__main__":
    main()