from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Avg, Max, Min, Count, Q
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView
from django.core.paginator import Paginator
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django_filters.views import FilterView
import json
from quiz.models import Quiz
from django.http import JsonResponse
from accounts.models import User, Student
from core.models import Session, Semester
from result.models import TakenCourse
from accounts.decorators import lecturer_required, student_required
from .forms import (
    ProgramForm,
    CourseAddForm,
    CourseAllocationForm,
    EditCourseAllocationForm,
    UploadFormFile,
    UploadFormVideo,
)
from .filters import ProgramFilter, CourseAllocationFilter
from .models import Program, Course, CourseAllocation, Upload, UploadVideo, Module, Chapter, Lesson
from .services import video_progress as video_progress_service
from django.http import JsonResponse
from .models import LessonProgress

from django.contrib.auth.decorators import user_passes_test

LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "te": "Telugu",
    "kn": "Kannada",
}

def lecturer_required(view_func):
    decorated_view_func = user_passes_test(
        lambda u: u.is_authenticated and (u.is_lecturer or u.is_superuser)
    )(view_func)
    return decorated_view_func

@method_decorator([login_required, lecturer_required], name="dispatch")
class ProgramFilterView(FilterView):
    filterset_class = ProgramFilter
    template_name = "course/program_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Programs"
        return context


@login_required
@lecturer_required
def program_add(request):
    if request.method == "POST":
        form = ProgramForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request, request.POST.get("title") + " program has been created."
            )
            return redirect("programs")
        else:
            messages.error(request, "Correct the error(S) below.")
    else:
        form = ProgramForm()

    return render(
        request,
        "course/program_add.html",
        {
            "title": "Add Program",
            "form": form,
        },
    )


@login_required
def program_detail(request, pk):
    program = Program.objects.get(pk=pk)
    courses = Course.objects.filter(program_id=pk).order_by("-year")
    credits = Course.objects.aggregate(Sum("credit"))

    paginator = Paginator(courses, 10)
    page = request.GET.get("page")

    courses = paginator.get_page(page)

    return render(
        request,
        "course/program_single.html",
        {
            "title": program.title,
            "program": program,
            "courses": courses,
            "credits": credits,
        },
    )


@login_required
@lecturer_required
def program_edit(request, pk):
    program = Program.objects.get(pk=pk)

    if request.method == "POST":
        form = ProgramForm(request.POST, instance=program)
        if form.is_valid():
            form.save()
            messages.success(
                request, str(request.POST.get("title")) + " program has been updated."
            )
            return redirect("programs")
    else:
        form = ProgramForm(instance=program)

    return render(
        request,
        "course/program_add.html",
        {"title": "Edit Program", "form": form},
    )


@login_required
@lecturer_required
def program_delete(request, pk):
    program = Program.objects.get(pk=pk)
    title = program.title
    program.delete()
    messages.success(request, "Program " + title + " has been deleted.")

    return redirect("programs")


# ########################################################


# ########################################################
# Course views
# ########################################################
@login_required
def course_single(request, slug):
    course = Course.objects.get(slug=slug)
    # files = Upload.objects.filter(course__slug=slug)
    #videos = list(UploadVideo.objects.filter(course__slug=slug))
    modules = course.modules.all()
    # lecturers = User.objects.filter(allocated_lecturer__pk=course.id)
    lecturers = CourseAllocation.objects.filter(courses__pk=course.id)

    # video_progress_map = {}
    # if request.user.is_authenticated and getattr(request.user, "is_student", False):
    #     student = Student.objects.filter(student=request.user).first()
    #     if student and TakenCourse.objects.filter(student=student, course=course).exists():
    #         video_progress_map = video_progress_service.progress_map_for_videos(
    #             student, [v.pk for v in videos]
    #         )

    # video_rows = [
    #     {"video": v, "progress_pct": video_progress_map.get(v.pk, 0)} for v in videos
    # ]

    return render(
        request,
        "course/course_single.html",
        {
            # "title": course.title,
            "course": course,
            # "files": files,
            #"videos": videos,
            # "video_rows": video_rows,
            "modules": modules,
            "lecturers": lecturers,
            # "media_url": settings.MEDIA_ROOT,
            # "video_progress_map": video_progress_map,
        },
    )


@login_required
@lecturer_required
def course_add(request, pk):


    users = User.objects.all()
    if request.method == "POST":
        form = CourseAddForm(request.POST)
        course_name = request.POST.get("title")
        course_code = request.POST.get("code")
        if form.is_valid():
            form.save()
            messages.success(
                request, (course_name + "(" + course_code + ")" + " has been created.")
            )
            return redirect("program_detail", pk=request.POST.get("program"))
        else:
            print("Form Errors:", form.errors)
            print("Non Field Errors:", form.non_field_errors())
            messages.error(request, "Correct the error(s) below.")
    else:
        form = CourseAddForm(initial={"program": Program.objects.get(pk=pk)})

    return render(
        request,
        "course/course_add.html",
        {
            "title": "Add Course",
            "form": form,
            "program": pk,
            "users": users,
        },
    )


@login_required
@lecturer_required
def course_edit(request, slug):
    course = get_object_or_404(Course, slug=slug)
    if request.method == "POST":
        form = CourseAddForm(request.POST, instance=course)
        course_name = request.POST.get("title")
        course_code = request.POST.get("code")
        if form.is_valid():
            form.save()
            messages.success(
                request, (course_name + "(" + course_code + ")" + " has been updated.")
            )
            return redirect("program_detail", pk=request.POST.get("program"))
        else:
            messages.error(request, "Correct the error(s) below.")
    else:
        form = CourseAddForm(instance=course)

    return render(
        request,
        "course/course_add.html",
        {
            "title": "Edit Course",
            # 'form': form, 'program': pk, 'course': pk
            "form": form,
        },
    )


@login_required
@lecturer_required
def course_delete(request, slug):
    course = Course.objects.get(slug=slug)
    # course_name = course.title
    course.delete()
    messages.success(request, "Course " + course.title + " has been deleted.")

    return redirect("program_detail", pk=course.program.id)


# ########################################################


# ########################################################
# Course Allocation
# ########################################################
@method_decorator([login_required], name="dispatch")
class CourseAllocationFormView(CreateView):
    form_class = CourseAllocationForm
    template_name = "course/course_allocation_form.html"

    def get_form_kwargs(self):
        kwargs = super(CourseAllocationFormView, self).get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form):
        # if a staff has been allocated a course before update it else create new
        lecturer = form.cleaned_data["lecturer"]
        selected_courses = form.cleaned_data["courses"]
        courses = ()
        for course in selected_courses:
            courses += (course.pk,)
        # print(courses)

        try:
            a = CourseAllocation.objects.get(lecturer=lecturer)
        except:
            a = CourseAllocation.objects.create(lecturer=lecturer)
        for i in range(0, selected_courses.count()):
            a.courses.add(courses[i])
            a.save()
        return redirect("course_allocation_view")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Assign Course"
        return context


@method_decorator([login_required], name="dispatch")
class CourseAllocationFilterView(FilterView):
    filterset_class = CourseAllocationFilter
    template_name = "course/course_allocation_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Course Allocations"
        return context


@login_required
@lecturer_required
def edit_allocated_course(request, pk):
    allocated = get_object_or_404(CourseAllocation, pk=pk)
    if request.method == "POST":
        form = EditCourseAllocationForm(request.POST, instance=allocated)
        if form.is_valid():
            form.save()
            messages.success(request, "course assigned has been updated.")
            return redirect("course_allocation_view")
    else:
        form = EditCourseAllocationForm(instance=allocated)

    return render(
        request,
        "course/course_allocation_form.html",
        {"title": "Edit Course Allocated", "form": form, "allocated": pk},
    )


@login_required
@lecturer_required
def deallocate_course(request, pk):
    course = CourseAllocation.objects.get(pk=pk)
    course.delete()
    messages.success(request, "successfully deallocate!")
    return redirect("course_allocation_view")


# ########################################################


# ########################################################
# File Upload views
# ########################################################
@login_required
@lecturer_required
def handle_file_upload(request, slug):
    course = Course.objects.get(slug=slug)
    if request.method == "POST":
        form = UploadFormFile(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.course = course
            obj.save()

            messages.success(
                request, (request.POST.get("title") + " has been uploaded.")
            )
            return redirect("course_detail", slug=slug)
    else:
        form = UploadFormFile()
    return render(
        request,
        "upload/upload_file_form.html",
        {"title": "File Upload", "form": form, "course": course},
    )


@login_required
@lecturer_required
def handle_file_edit(request, slug, file_id):
    course = Course.objects.get(slug=slug)
    instance = Upload.objects.get(pk=file_id)
    if request.method == "POST":
        form = UploadFormFile(request.POST, request.FILES, instance=instance)
        # file_name = request.POST.get('name')
        if form.is_valid():
            form.save()
            messages.success(
                request, (request.POST.get("title") + " has been updated.")
            )
            return redirect("course_detail", slug=slug)
    else:
        form = UploadFormFile(instance=instance)

    return render(
        request,
        "upload/upload_file_form.html",
        {"title": instance.title, "form": form, "course": course},
    )


@login_required
@lecturer_required
def handle_file_delete(request, slug, file_id):
    file = Upload.objects.get(pk=file_id)
    # file_name = file.name
    file.delete()

    messages.success(request, (file.title + " has been deleted."))
    return redirect("course_detail", slug=slug)


# ########################################################
# Video Upload views
# ########################################################
@login_required
@lecturer_required
def handle_video_upload(request, lesson_id):
    # course = Course.objects.get(slug=slug)
    lesson = get_object_or_404(Lesson, id=lesson_id)
    course = lesson.chapter.module.course
    if request.method == "POST":
        form = UploadFormVideo(request.POST, request.FILES)
        
        if form.is_valid():
            obj = form.save(commit=False)

            obj.course = course
            obj.lesson = lesson

            # Save selected languages
            selected_languages = form.cleaned_data.get("selected_languages", [])
            obj.selected_languages = selected_languages

            obj.save()

            messages.success(
                request, (request.POST.get("title") + " has been uploaded.")
            )
            
            return redirect("lesson_detail", lesson_id=lesson.id)
    else:
        form = UploadFormVideo()

    return render(
        request,
        "upload/upload_video_form.html",
        {"title": "Video Upload", "form": form, "course": course},
    )


@login_required
def handle_video_single(request, slug, video_slug):
    course = get_object_or_404(Course, slug=slug)
    video = get_object_or_404(UploadVideo, slug=video_slug, course=course)

    tracker = False
    initial = {"position_seconds": 0.0, "duration_seconds": 0.0, "progress_percent": 0}
    if request.user.is_authenticated and getattr(request.user, "is_student", False):
        student = Student.objects.filter(student=request.user).first()
        if student and video_progress_service.student_can_track_video(student, video):
            tracker = True
            row = video_progress_service.get_progress(student, video)
            if row:
                initial = {
                    "position_seconds": float(row.position_seconds),
                    "duration_seconds": float(row.duration_seconds),
                    "progress_percent": int(row.progress_percent),
                }

    return render(
        request,
        "upload/video_single.html",
        {
            "course": course,
            "video": video,
            "video_progress_tracker": tracker,
            "video_initial_progress": initial,
        },
    )


@login_required
@lecturer_required
def handle_video_edit(request, slug, video_slug):
    course = Course.objects.get(slug=slug)
    instance = UploadVideo.objects.get(slug=video_slug)
    if request.method == "POST":
        form = UploadFormVideo(request.POST, request.FILES, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(
                request, (request.POST.get("title") + " has been updated.")
            )
            return redirect("course_detail", slug=slug)
    else:
        form = UploadFormVideo(instance=instance)

    return render(
        request,
        "upload/upload_video_form.html",
        {"title": instance.title, "form": form, "course": course},
    )


@login_required
@lecturer_required
def handle_video_delete(request, slug, video_slug):
    video = get_object_or_404(UploadVideo, slug=video_slug)
    # video = UploadVideo.objects.get(slug=video_slug)
    video.delete()

    messages.success(request, (video.title + " has been deleted."))
    return redirect("course_detail", slug=slug)


# ########################################################


# ########################################################
# Course Registration
# ########################################################
@login_required
@student_required
def course_registration(request):
    if request.method == "POST":
        student = Student.objects.get(student__pk=request.user.id)
        ids = ()
        data = request.POST.copy()
        data.pop("csrfmiddlewaretoken", None)  # remove csrf_token
        for key in data.keys():
            ids = ids + (str(key),)
        for s in range(0, len(ids)):
            course = Course.objects.get(pk=ids[s])

            already_enrolled = TakenCourse.objects.filter(
                student=student,
                course=course
            ).exists()

            if not already_enrolled:
                TakenCourse.objects.create(
                    student=student,
                    course=course
                )
        messages.success(request, "Courses registered successfully!")
        return redirect("course_registration")
    else:
        current_semester = Semester.objects.filter(is_current_semester=True).first()
        if not current_semester:
            messages.error(request, "No active semester found.")
            return render(request, "course/course_registration.html")

        # student = Student.objects.get(student__pk=request.user.id)
        student = get_object_or_404(Student, student__id=request.user.id)
        taken_courses = TakenCourse.objects.filter(student__student__id=request.user.id)
        t = ()
        for i in taken_courses:
            t += (i.course.pk,)

        courses = (
            # Course.objects.filter(
            #     # program__pk=student.program.id,
            #     # level=student.level.replace(" Degree", ""),
            #     semester=current_semester.semester,
            # )
            # .exclude(id__in=t)
            # .order_by("year")
            Course.objects.filter(
                Q(
                    level=student.level,
                    program__pk=student.program.id
                )
                | Q(id__in=t)
            ).order_by("year")
        )
        all_courses = Course.objects.filter(
            level=student.level, program__pk=student.program.id
        )

        no_course_is_registered = False  # Check if no course is registered
        all_courses_are_registered = False

        registered_courses = Course.objects.filter(level=student.level).filter(id__in=t)
        if (
            registered_courses.count() == 0
        ):  # Check if number of registered courses is 0
            no_course_is_registered = True

        if registered_courses.count() == all_courses.count():
            all_courses_are_registered = True

        total_first_semester_credit = 0
        total_sec_semester_credit = 0
        total_registered_credit = 0
        for i in courses:
            if i.semester == "First":
                total_first_semester_credit += int(i.credit)
            if i.semester == "Second":
                total_sec_semester_credit += int(i.credit)
        for i in registered_courses:
            total_registered_credit += int(i.credit)

        print("Student Program:", student.program.id)
        print("Student Level:", student.level)
        print("Current Semester:", current_semester.semester)
        print("Courses Found:", courses)
        context = {
            "is_calender_on": True,
            "all_courses_are_registered": all_courses_are_registered,
            "no_course_is_registered": no_course_is_registered,
            "current_semester": current_semester,
            "courses": courses,
            "total_first_semester_credit": total_first_semester_credit,
            "total_sec_semester_credit": total_sec_semester_credit,
            "registered_courses": registered_courses,
            "total_registered_credit": total_registered_credit,
            "student": student,
            "taken_courses": taken_courses,
        }
        return render(request, "course/course_registration.html", context)


@login_required
@student_required
def course_drop(request):
    if request.method == "POST":
        student = Student.objects.get(student__pk=request.user.id)
        ids = ()
        data = request.POST.copy()
        data.pop("csrfmiddlewaretoken", None)  # remove csrf_token
        for key in data.keys():
            ids = ids + (str(key),)
        for s in range(0, len(ids)):
            course = Course.objects.get(pk=ids[s])
            obj = TakenCourse.objects.get(student=student, course=course)
            obj.delete()
        messages.success(request, "Successfully Dropped!")
        return redirect("course_registration")


# ########################################################


@login_required
def user_course_list(request):
    if request.user.is_lecturer:
        courses = Course.objects.filter(allocated_course__lecturer__pk=request.user.id)

        return render(request, "course/user_course_list.html", {"courses": courses})

    elif request.user.is_student:
        #student = Student.objects.get(student__pk=request.user.id)
        student = Student.objects.filter(student=request.user).first()


        if not student:
            messages.error(request, "Student profile not found. Contact admin.")
            return redirect("profile")

        if not student.program:
            messages.error(request, "Program not assigned yet.")
            return redirect("profile")
        

        
        taken_courses = TakenCourse.objects.filter(
            student__student__id=student.student.id
        )
        courses = Course.objects.filter(
            level=student.level,
            program__pk=student.program.id
        )
        # course_progress = []
        # for tc in taken_courses:
        #     course_obj = tc.course
        #     # course_obj = Course.objects.filter(title=tc.course).first()

        #     # if not course_obj:
        #     #     tc.progress = 0
        #     #     continue
        #     #course_obj = Course.objects.get(title=course_obj)

        #     total_lessons = Lesson.objects.filter(chapter__module__course=course_obj).count()

        #     # completed_lessons = LessonCompletion.objects.filter(
        #     #     student=request.user,
        #     #     lesson__chapter__module__course=course_obj,
        #     #     completed=True
        #     # ).count()

        #     progress = 0
        #     if total_lessons > 0:
        #         progress = int((completed_lessons / total_lessons) * 100)

        #     course_progress.append({
        #         "course": course_obj,
        #         "progress": progress
        #     })

        return render(
            request,
            "course/user_course_list.html",
            {"student": student, "taken_courses": taken_courses, "courses": courses},
        )

    else:
        return render(request, "course/user_course_list.html")

@login_required
@lecturer_required
def add_module(request, course_id):
    course = Course.objects.get(id=course_id)

    if request.method == "POST":
        title = request.POST.get("title")

        # module = Module.objects.create(title=title)
        # course.modules.add(module)
        if title:
            Module.objects.create(
                title=title,
                course=course   
            )

        return redirect("course_detail", slug=course.slug)

    return render(request, "course/add_module.html", {"course": course})


@login_required
@lecturer_required
def add_chapter(request, module_id):
    module = get_object_or_404(Module, id=module_id)

    if request.method == "POST":
        title = request.POST.get("title")
        if title:
            Chapter.objects.create(title=title, module=module)
            messages.success(request, "Chapter added successfully")
            return redirect("chapter_list", module_id=module.id)

    return render(request, "course/add_chapter.html", {"module": module})


@login_required
@lecturer_required
def add_lesson(request, chapter_id):
    chapter = get_object_or_404(Chapter, id=chapter_id)

    if request.method == "POST":
        title = request.POST.get("title")
        if title:
            Lesson.objects.create(title=title, chapter=chapter)
            messages.success(request, "Lesson added successfully")
            return redirect("lesson_list", chapter_id=chapter.id)

    return render(request, "course/add_lesson.html", {"chapter": chapter})


# def module_list(request, course_slug):
#     course = Course.objects.get(slug=course_slug)
#     modules = course.modules.all()

#     return render(request, "course/module_list.html", {
#         "course": course,
#         "modules": modules
#     })


# def chapter_list(request, module_id):
#     module = Module.objects.get(id=module_id)
#     chapters = module.chapters.all()

#     return render(request, "course/chapter_list.html", {
#         "module": module,
#         "chapters": chapters
#     })


# def lesson_list(request, chapter_id):
#     chapter = Chapter.objects.get(id=chapter_id)
#     lessons = chapter.lessons.all()

#     return render(request, "course/lesson_list.html", {
#         "chapter": chapter,
#         "lessons": lessons
#     })


# def lesson_detail(request, lesson_id):
#     lesson = Lesson.objects.get(id=lesson_id)

#     return render(request, "course/lesson_detail.html", {
#         "lesson": lesson
#     })


@login_required
def module_list(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    modules = course.modules.all()

    return render(request, "course/module_list.html", {
        "course": course,
        "modules": modules
    })

@login_required
def chapter_list(request, module_id):
    module = get_object_or_404(Module, id=module_id)
    chapters = module.chapters.all()

    return render(request, "course/chapter_list.html", {
        "module": module,
        "chapters": chapters
    })

@login_required
def lesson_list(request, chapter_id):
    chapter = Chapter.objects.get(id=chapter_id)
    lessons = chapter.lessons.all()

    if request.method == "POST":
        lesson_id = request.POST.get("lesson_id")
        lesson = Lesson.objects.get(id=lesson_id)

        obj, created = LessonCompletion.objects.get_or_create(
            student=request.user,
            lesson=lesson
        )
        obj.completed = True
        obj.save()

    # completed_lessons = LessonCompletion.objects.filter(
    #     student=request.user,
    #     lesson__in=lessons,
    #     completed=True
    # ).values_list('lesson_id', flat=True)

    return render(request, "course/lesson_list.html", {
        "chapter": chapter,
        "lessons": lessons,
        #"completed_lessons": completed_lessons
    })
# def lesson_list(request, chapter_id):
#     chapter = get_object_or_404(Chapter, id=chapter_id)
#     lessons = chapter.lessons.all()

#     return render(request, "course/lesson_list.html", {
#         "chapter": chapter,
#         "lessons": lessons
#     })

@login_required
def lesson_detail(request, lesson_id):
    
    lesson = get_object_or_404(Lesson, id=lesson_id)
    # all_lessons = list(
    #     Lesson.objects.filter(
    #         chapter__module__course=lesson.chapter.module.course
    #     ).order_by("id")
    # )

    # current_index = all_lessons.index(lesson)

    # is_unlocked = True

    # if current_index > 0:

    #     previous_lesson = all_lessons[current_index - 1]

    #     is_unlocked = LessonProgress.objects.filter(
    #         student=request.user,
    #         lesson=previous_lesson,
    #         completed=True
    # ).exists()

    videos = lesson.uploadvideo_set.all()
    LANGUAGE_NAMES = {
        "hi": "Hindi",
        "te": "Telugu",
        "kn": "Kannada",
    }

    for video in videos:
        video.available_languages = [
            {"code": lang, "name": LANGUAGE_NAMES.get(lang, lang)}
            for lang in (video.selected_languages or [])
        ]
    # unlocked_video_ids = []

    # for index, video in enumerate(videos):

    #     if index == 0:
    #         unlocked_video_ids.append(video.id)
    #         continue

    #     previous_video = videos[index - 1]

    #     previous_completed = LessonProgress.objects.filter(
    #         student=request.user,
    #         lesson=lesson,
    #         completed=True
    #     ).exists()

    #     if previous_completed:
    #         unlocked_video_ids.append(video.id)

    
    files = lesson.upload_set.all()
    course = lesson.chapter.module.course
    modules = Module.objects.filter(course=course).order_by("order")
    obj = None
    lesson_progress = LessonProgress.objects.filter(
        student=request.user,
        lesson=lesson
    ).first()


    # if request.user.is_authenticated:
    #     LessonCompletion.objects.update_or_create(
    #         student=request.user,
    #         lesson=lesson,
    #         defaults={"completed": True},
            
    #     )

    completed_lessons = LessonProgress.objects.filter(
        student=request.user,
        completed=True
    ).values_list("lesson_id", flat=True)


    total_course_lessons = Lesson.objects.filter(
        chapter__module__course=course
    ).count()

    completed_course_lessons = LessonProgress.objects.filter(
        student=request.user,
        lesson__chapter__module__course=course,
        completed=True
    ).count()

    course_progress = 0

    if total_course_lessons > 0:
        course_progress = int(
            (completed_course_lessons / total_course_lessons) * 100
        )

    # if not is_unlocked:

    #     messages.error(
    #         request,
    #         "Complete the previous lesson first."
    #     )

    #     return redirect(
    #         "lesson_detail",
    #         lesson_id=previous_lesson.id
    #     )

    module_progress = {}
    module_completed = {}

    for module in modules:
        total_lessons = Lesson.objects.filter(
            chapter__module=module
        ).count()

        completed = LessonProgress.objects.filter(
            student=request.user,
            lesson__chapter__module=module,
            completed=True
        ).count()

        percent = 0

        if total_lessons > 0:
            percent = int((completed / total_lessons) * 100)

        module_progress[module.id] = percent

        module_completed[module.id] = (
            total_lessons > 0 and completed == total_lessons
    )


    lesson_durations = {}

    for module in modules:
        for chapter in module.chapters.all():
            for lesson_obj in chapter.lessons.all():

                total_duration = sum(
                    video.duration
                    for video in lesson_obj.uploadvideo_set.all()
                )

                mins = total_duration // 60
                secs = total_duration % 60

                lesson_durations[lesson_obj.id] = f"{mins}:{secs:02d}"


    module_durations = {}

    for module in modules:

        total_module_duration = 0

        for chapter in module.chapters.all():
            for lesson_obj in chapter.lessons.all():

                lesson_duration = sum(
                    video.duration
                    for video in lesson_obj.uploadvideo_set.all()
                )

                total_module_duration += lesson_duration

        mins = total_module_duration // 60
        secs = total_module_duration % 60

        module_durations[module.id] = f"{mins}:{secs:02d}"

    

    all_lessons = []

    for module in modules:
        for chapter in module.chapters.all():
            for lesson_obj in chapter.lessons.all():
                all_lessons.append(lesson_obj)

    current_index = all_lessons.index(lesson)

    previous_lesson = (
        all_lessons[current_index - 1]
        if current_index > 0
        else None
    )

    next_lesson = (
        all_lessons[current_index + 1]
        if current_index < len(all_lessons) - 1
        else None
    )

    course_total_duration = 0

    for module in modules:
        for chapter in module.chapters.all():
            for lesson_obj in chapter.lessons.all():

                lesson_duration = sum(
                    video.duration
                    for video in lesson_obj.uploadvideo_set.all()
                )

                course_total_duration += lesson_duration

    hours = course_total_duration // 3600
    minutes = (course_total_duration % 3600) // 60

    course_duration = f"{hours}h {minutes}m"

    from quiz.models import Quiz

    all_quizzes = Quiz.objects.filter(course=course)

    lesson_quiz = Quiz.objects.filter(
        lesson=lesson,
        draft=False
    ).first()

    chapter_quiz = Quiz.objects.filter(
        chapter=lesson.chapter,
        draft=False
    ).first()

    module_quiz = Quiz.objects.filter(
        module=lesson.chapter.module,
        draft=False
    ).first()



    return render(request, "course/lesson_detail.html", {
        "lesson": lesson,
        "videos": videos,
        "files": files,
        "course": course,
        "modules": modules,

        "saved_time": lesson_progress.watched_seconds if lesson_progress else 0,
        "saved_percent": lesson_progress.progress_percent if lesson_progress else 0,
        "lesson_progress": lesson_progress,
        "completed_lessons": completed_lessons,
        "course_progress": course_progress,
        
        "module_progress": module_progress,
        "module_completed": module_completed,
        "lesson_durations": lesson_durations,
        
        "module_durations": module_durations,
        "previous_lesson": previous_lesson,
        "next_lesson": next_lesson,
        "course_duration": course_duration,

        "lesson_quiz": lesson_quiz,
        "chapter_quiz": chapter_quiz,
        "module_quiz": module_quiz,
        "all_quizzes": all_quizzes,


        
    })


@login_required
def save_video_duration(request):

    if request.method == "POST":

        video_id = request.POST.get("video_id")
        duration = request.POST.get("duration")

        try:
            video = UploadVideo.objects.get(id=video_id)

            if video.duration == 0:
                video.duration = int(float(duration))
                video.save()

                # Update Lesson
                lesson = video.lesson
                lesson.duration = sum(
                    v.duration
                    for v in lesson.uploadvideo_set.all()
                )
                lesson.save()

                # Update Module
                module = lesson.chapter.module
                module.duration = sum(
                    l.duration
                    for chapter in module.chapters.all()
                    for l in chapter.lessons.all()
                )
                module.save()

                # Update Course
                course = module.course
                course.duration = sum(
                    m.duration
                    for m in course.modules.all()
                )
                course.save()

            return JsonResponse({"status": "success"})

        except Exception as e:
            return JsonResponse({
                "status": "error",
                "message": str(e)
            })

    return JsonResponse({"status": "invalid"})

@login_required
def save_progress(request):

    print("SAVE PROGRESS HIT")

    if request.method == "POST":

        lesson_id = request.POST.get("lesson_id")
        current_time = float(request.POST.get("current_time", 0))
        duration = float(request.POST.get("duration", 0))

        if duration == 0:
            return JsonResponse({"status": "error"})

        percent = round((current_time / duration) * 100)

        lesson = Lesson.objects.get(id=lesson_id)

        progress_obj, created = LessonProgress.objects.get_or_create(
            student=request.user,
            lesson=lesson
        )

        # Once completed, keep it completed forever
        if progress_obj.completed:

            progress_obj.progress_percent = 100

        else:

            # Never allow progress to go backwards
            if percent > progress_obj.progress_percent:
                progress_obj.progress_percent = percent
                progress_obj.watched_seconds = current_time

            if percent >= 90:
                progress_obj.completed = True
                progress_obj.progress_percent = 100

        progress_obj.save()

        return JsonResponse({
            "status": "success",
            "progress": progress_obj.progress_percent,
            "completed": progress_obj.completed
        })

    return JsonResponse({
        "status": "invalid request"
    })


# @login_required
# def course_learn(request, course_id):
#     course = get_object_or_404(Course, id=course_id)

#     first_lesson = Lesson.objects.filter(
#         chapter__module__course=course
#     ).order_by(
#         "chapter__module__order",
#         "chapter__order",
#         "order"
#     ).first()

#     if first_lesson:
#         return redirect("lesson_detail", lesson_id=first_lesson.id)

#     messages.warning(request, "No lessons found in this course.")
#     return redirect("home")


@login_required
def course_start(request, slug):

    course = get_object_or_404(Course, slug=slug)

    first_lesson = Lesson.objects.filter(
        chapter__module__course=course
    ).order_by(
        "chapter__module__order",
        "chapter__order",
        "order"
    ).first()

    if first_lesson:
        return redirect("lesson_detail", lesson_id=first_lesson.id)

    messages.warning(request, "No lessons available.")
    return redirect("user_course_list")


# def get_course_progress(student, course):
#     total_lessons = Lesson.objects.filter(module__course=course).count()

#     completed_lessons = LessonCompletion.objects.filter(
#         student=student,
#         lesson__module__course=course,
#         completed=True
#     ).count()

#     if total_lessons == 0:
#         return 0

#     return round((completed_lessons / total_lessons) * 100, 2)

    

# def update_progress(request, lesson_id):
#     if request.method == "POST":
#         data = json.loads(request.body)
#         progress = data.get("progress", 0)
#         time = data.get("time", 0)

#         obj, created = LessonCompletion.objects.get_or_create(
#             student=request.user,
#             lesson_id=lesson_id
#         )

#         obj.progress = progress
#         obj.last_time = time

#         if progress >= 95:
#             obj.completed = True

#         obj.save()

#         return JsonResponse({"status": "ok"})

# def mark_complete(request, lesson_id):
#     if request.method == "POST":
#         obj, created = LessonCompletion.objects.get_or_create(
#             student=request.user,
#             lesson_id=lesson_id
#         )

#         obj.completed = True
#         obj.progress = 100
#         obj.save()

#         return JsonResponse({"status": "completed"})