import json
import threading
import time
from .evaluator.interactive_runner import InteractiveRunner
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import (
    render,
    redirect,
    get_object_or_404,
)

from .models import (
    Assessment,
    AssessmentQuestion,
    QuestionOption,
    TestCase,
    AssessmentPlacement,
    AssessmentSubmission,
    QuestionSubmission,
)

from .forms import (
    AssessmentForm,
    AssessmentQuestionForm,
    QuestionOptionForm,
    TestCaseForm,
    AssessmentPlacementForm,
)

from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .evaluator.programming_evaluator import (
    evaluate_programming_question,
)
from .evaluator.theory_evaluator import evaluate_theory_answer

from .evaluator.comparator import compare_output

from django.http import JsonResponse

from .evaluator import get_runner
from django.urls import reverse
from django.db import models
from .evaluator.code_quality_evaluator import evaluate_code_quality

# ==========================================================
# INTERACTIVE CODE SESSIONS
# ==========================================================

interactive_sessions = {}

interactive_sessions_lock = threading.Lock()

interactive_runner = InteractiveRunner()


def update_assessment_total_marks(assessment):
    assessment.total_marks = (
        assessment.questions.aggregate(
            total=models.Sum("marks")
        )["total"] or 0
    )
    assessment.save(update_fields=["total_marks"])


def cleanup_expired_interactive_sessions():

    now = time.time()

    expired_sessions = []

    with interactive_sessions_lock:

        for session_id, session_data in interactive_sessions.items():

            session = session_data["session"]

            if session.is_expired():

                expired_sessions.append(
                    session_id
                )

    for session_id in expired_sessions:

        stop_interactive_session(
            session_id
        )


def stop_interactive_session(session_id):

    with interactive_sessions_lock:

        session_data = interactive_sessions.pop(
            session_id,
            None
        )

    if session_data:

        try:

            session_data["session"].stop()

        except Exception:

            pass

# ==========================================================
# ASSESSMENT LIST
# ==========================================================

@login_required
def assessment_list(request):

    if not (
        request.user.is_lecturer
        or request.user.is_superuser
    ):
        messages.error(
            request,
            "You do not have permission to access assessment management."
        )

        return redirect(
            "student_assessment_list"
        )

    assessments = Assessment.objects.filter(
        created_by=request.user
    ).order_by("-created_at")

    return render(
        request,
        "assessment/assessment_list.html",
        {
            "assessments": assessments,
        }
    )


# ==========================================================
# CREATE ASSESSMENT
# ==========================================================

@login_required
def assessment_create(request):

    if request.method == "POST":

        form = AssessmentForm(request.POST)

        if form.is_valid():

            assessment = form.save(commit=False)

            assessment.created_by = request.user

            assessment.save()

            messages.success(
                request,
                "Assessment created successfully."
            )

            return redirect(
                "assessment_detail",
                pk=assessment.pk
            )

    else:

        form = AssessmentForm()

    return render(
        request,
        "assessment/assessment_form.html",
        {
            "form": form,
            "is_edit": False,
        }
    )


# ==========================================================
# EDIT ASSESSMENT
# ==========================================================

@login_required
def assessment_edit(request, pk):

    assessment = get_object_or_404(
        Assessment,
        pk=pk,
        created_by=request.user
    )

    if request.method == "POST":

        form = AssessmentForm(
            request.POST,
            instance=assessment
        )

        if form.is_valid():

            form.save()

            update_assessment_total_marks(assessment)

            messages.success(
                request,
                "Assessment updated successfully."
            )

            return redirect(
                "assessment_detail",
                pk=assessment.pk
            )

    else:

        form = AssessmentForm(
            instance=assessment
        )

    return render(
        request,
        "assessment/assessment_form.html",
        {
            "form": form,
            "assessment": assessment,
            "is_edit": True,
        }
    )


# ==========================================================
# DELETE ASSESSMENT
# ==========================================================

@login_required
def assessment_delete(request, pk):

    assessment = get_object_or_404(
        Assessment,
        pk=pk,
        created_by=request.user
    )

    if request.method == "POST":

        assessment.delete()

        messages.success(
            request,
            "Assessment deleted successfully."
        )

        return redirect("assessment_list")

    return render(
        request,
        "assessment/assessment_confirm_delete.html",
        {
            "assessment": assessment,
        }
    )


# ==========================================================
# ASSESSMENT DETAIL
# ==========================================================

@login_required
def assessment_detail(request, pk):

    assessment = get_object_or_404(
        Assessment,
        pk=pk,
        created_by=request.user
    )

    questions = assessment.questions.all()
    placements = assessment.placements.all()

    return render(
        request,
        "assessment/assessment_detail.html",
        {
            "assessment": assessment,
            "questions": questions,
            "placements": placements,
        }
    )


# ==========================================================
# CREATE QUESTION
# ==========================================================
@login_required
def question_create(request, assessment_id):

    assessment = get_object_or_404(
        Assessment,
        pk=assessment_id,
        created_by=request.user
    )

    if request.method == "POST":

        form = AssessmentQuestionForm(
            request.POST
        )

        if form.is_valid():

            question = form.save(
                commit=False
            )

            question.assessment = assessment
            question.save()

            # ------------------------------------------------
            # MCQ OPTIONS
            # ------------------------------------------------

            if question.question_type == "MCQ":

                option_texts = request.POST.getlist(
                    "option_text[]"
                )

                correct_option = request.POST.get(
                    "correct_option"
                )

                for index, option_text in enumerate(
                    option_texts
                ):

                    option_text = option_text.strip()

                    if option_text:

                        QuestionOption.objects.create(
                            question=question,
                            option_text=option_text,
                            is_correct=(
                                str(index)
                                == str(correct_option)
                            ),
                            order=index + 1
                        )

            # ------------------------------------------------
            # MULTIPLE SELECT
            # ------------------------------------------------

            elif question.question_type == "MULTIPLE_SELECT":

                option_texts = request.POST.getlist(
                    "multiple_option_text[]"
                )

                correct_options = request.POST.getlist(
                    "correct_multiple_options[]"
                )

                for index, option_text in enumerate(
                    option_texts
                ):

                    option_text = option_text.strip()

                    if option_text:

                        QuestionOption.objects.create(
                            question=question,
                            option_text=option_text,
                            is_correct=(
                                str(index)
                                in correct_options
                            ),
                            order=index + 1
                        )

            # ------------------------------------------------
            # FILL BLANK
            # ------------------------------------------------

            elif question.question_type == "FILL_BLANK":

                accepted_answers = request.POST.getlist(
                    "accepted_answers[]"
                )

                question.evaluation_criteria = {
                    "accepted_answers": [
                        answer.strip()
                        for answer in accepted_answers
                        if answer.strip()
                    ]
                }

                question.save()

            # ------------------------------------------------
            # THEORY
            # ------------------------------------------------

            elif question.question_type == "THEORY":

                criteria_names = request.POST.getlist(
                    "criteria_name[]"
                )

                criteria_marks = request.POST.getlist(
                    "criteria_marks[]"
                )

                criteria = []

                for name, marks in zip(
                    criteria_names,
                    criteria_marks
                ):

                    if name.strip():

                        criteria.append({
                            "name": name.strip(),
                            "marks": marks
                        })

                question.evaluation_criteria = criteria

                question.save()

            # ------------------------------------------------
            # PROGRAMMING TEST CASES
            # ------------------------------------------------

            elif question.question_type == "PROGRAMMING":

                inputs = request.POST.getlist(
                    "test_input[]"
                )

                outputs = request.POST.getlist(
                    "test_output[]"
                )

                marks = request.POST.getlist(
                    "test_marks[]"
                )

                hidden_values = request.POST.getlist(
                    "test_hidden[]"
                )

                total_test_case_marks = 0

                # ------------------------------------------------
                # CALCULATE TOTAL TEST CASE MARKS
                # ------------------------------------------------

                for index, input_data in enumerate(inputs):

                    if index >= len(outputs):
                        continue

                    if (
                        not input_data.strip()
                        and not outputs[index].strip()
                    ):
                        continue

                    test_case_marks = (
                        int(marks[index])
                        if index < len(marks)
                        and marks[index]
                        else 0
                    )

                    total_test_case_marks += test_case_marks

                # ------------------------------------------------
                # VALIDATE PROGRAMMING MARK ALLOCATION
                # ------------------------------------------------

                total_allocated_marks = (
                    question.ai_evaluation_marks
                    + total_test_case_marks
                )

                if total_allocated_marks > question.marks:

                    question.delete()

                    messages.error(
                        request,
                        (
                            f"Cannot save programming question. "
                            f"AI evaluation marks "
                            f"({question.ai_evaluation_marks}) + "
                            f"test case marks "
                            f"({total_test_case_marks}) = "
                            f"{total_allocated_marks} marks, "
                            f"which exceeds the question's assigned "
                            f"{question.marks} marks."
                        )
                    )

                    return render(
                        request,
                        "assessment/question_form.html",
                        {
                            "form": form,
                            "assessment": assessment,
                            "is_edit": False,
                        }
                    )

                # ------------------------------------------------
                # CREATE TEST CASES
                # ------------------------------------------------

                for index, input_data in enumerate(inputs):

                    if index >= len(outputs):
                        continue

                    if (
                        not input_data.strip()
                        and not outputs[index].strip()
                    ):
                        continue

                    TestCase.objects.create(
                        question=question,
                        input_data=input_data,
                        expected_output=outputs[index],
                        marks=(
                            int(marks[index])
                            if index < len(marks)
                            and marks[index]
                            else 0
                        ),
                        is_hidden=(
                            hidden_values[index] == "1"
                            if index < len(hidden_values)
                            else True
                        ),
                        order=index + 1
                    )

            # ------------------------------------------------
            # UPDATE ASSESSMENT TOTAL MARKS
            # ------------------------------------------------

            update_assessment_total_marks(
                assessment
            )

            messages.success(
                request,
                "Question saved successfully."
            )

            return redirect(
                "assessment_edit",
                pk=assessment.id
            )

    else:

        form = AssessmentQuestionForm(
            initial={
                "order": assessment.questions.count() + 1
            }
        )

    return render(
        request,
        "assessment/question_form.html",
        {
            "form": form,
            "assessment": assessment,
            "is_edit": False,
        }
    )

# ==========================================================
# EDIT QUESTION
# ==========================================================

@login_required
def question_edit(request, question_id):

    question = get_object_or_404(
        AssessmentQuestion,
        pk=question_id,
        assessment__created_by=request.user
    )

    assessment = question.assessment

    if request.method == "POST":

        form = AssessmentQuestionForm(
            request.POST,
            instance=question
        )

        if form.is_valid():

            updated_question = form.save(commit=False)

            # ------------------------------------------------
            # PROGRAMMING QUESTION MARK VALIDATION
            # ------------------------------------------------
            if updated_question.question_type == "PROGRAMMING":

                existing_test_case_marks = (
                    question.test_cases.aggregate(
                        total=models.Sum("marks")
                    )["total"] or 0
                )

                total_allocated_marks = (
                    updated_question.ai_evaluation_marks
                    + existing_test_case_marks
                )

                if total_allocated_marks > updated_question.marks:

                    available_test_case_marks = (
                        updated_question.marks
                        - updated_question.ai_evaluation_marks
                    )

                    messages.error(
                        request,
                        (
                            f"Cannot update question. "
                            f"AI evaluation marks "
                            f"({updated_question.ai_evaluation_marks}) "
                            f"+ existing test case marks "
                            f"({existing_test_case_marks}) "
                            f"= {total_allocated_marks} marks, "
                            f"which exceeds the question's assigned "
                            f"{updated_question.marks} marks. "
                            f"Only {max(available_test_case_marks, 0)} "
                            f"marks are available for test cases."
                        )
                    )

                    return render(
                        request,
                        "assessment/question_form.html",
                        {
                            "form": form,
                            "assessment": assessment,
                            "question": question,
                            "is_edit": True,
                        }
                    )

            # ------------------------------------------------
            # SAVE QUESTION
            # ------------------------------------------------

            updated_question.save()

            # ------------------------------------------------
            # UPDATE ASSESSMENT TOTAL
            # ------------------------------------------------

            update_assessment_total_marks(assessment)

            messages.success(
                request,
                "Question updated successfully."
            )

            return redirect(
                "assessment_detail",
                pk=assessment.pk
            )

    else:

        form = AssessmentQuestionForm(
            instance=question
        )

    return render(
        request,
        "assessment/question_form.html",
        {
            "form": form,
            "assessment": assessment,
            "question": question,
            "is_edit": True,
        }
    )


# ==========================================================
# DELETE QUESTION
# ==========================================================

@login_required
def question_delete(request, question_id):

    question = get_object_or_404(
        AssessmentQuestion,
        pk=question_id,
        assessment__created_by=request.user
    )

    assessment = question.assessment

    if request.method == "POST":

        question.delete()

        update_assessment_total_marks(assessment)

        messages.success(
            request,
            "Question deleted successfully."
        )

        return redirect(
            "assessment_detail",
            pk=assessment.pk
        )

    return render(
        request,
        "assessment/question_confirm_delete.html",
        {
            "question": question,
            "assessment": assessment,
        }
    )


# ==========================================================
# CREATE TEST CASE
# ==========================================================

@login_required
def test_case_create(request, question_id):

    question = get_object_or_404(
        AssessmentQuestion,
        pk=question_id,
        assessment__created_by=request.user
    )

    if question.question_type != "PROGRAMMING":

        messages.error(
            request,
            "Test cases can only be added to programming questions."
        )

        return redirect(
            "assessment_detail",
            pk=question.assessment.pk
        )

    if request.method == "POST":

        form = TestCaseForm(
            request.POST
        )

        if form.is_valid():
            test_case_marks = form.cleaned_data.get("marks") or 0

            existing_test_case_marks = (
                question.test_cases.aggregate(
                    total=models.Sum("marks")
                )["total"] or 0
            )

            available_test_case_marks = (
                question.marks
                - question.ai_evaluation_marks
                - existing_test_case_marks
            )

            if test_case_marks > available_test_case_marks:
                messages.error(
                    request,
                    (
                        f"Cannot add this test case. You are assigning "
                        f"{test_case_marks} marks, but only "
                        f"{max(available_test_case_marks, 0)} marks are available "
                        f"for test cases in this question. "
                        f"Question marks: {question.marks}, "
                        f"AI evaluation marks: {question.ai_evaluation_marks}, "
                        f"Existing test case marks: {existing_test_case_marks}."
                    )
                )
            else:
                test_case = form.save(commit=False)
                test_case.question = question
                test_case.order = question.test_cases.count() + 1
                test_case.save()

                messages.success(
                    request,
                    f"Test Case {test_case.order} saved successfully."
                )

                return redirect(
                    "test_case_create",
                    question_id=question.pk
                )

    else:

        form = TestCaseForm()

    public_test_cases = question.test_cases.filter(
        is_hidden=False
    )

    hidden_test_cases = question.test_cases.filter(
        is_hidden=True
    )

    return render(
        request,
        "assessment/test_case_form.html",
        {
            "form": form,
            "question": question,
            "assessment": question.assessment,
            "public_test_cases": public_test_cases,
            "hidden_test_cases": hidden_test_cases,
        }
    )

# ==========================================================
# EDIT TEST CASE
# ==========================================================

@login_required
def test_case_edit(request, test_case_id):

    test_case = get_object_or_404(
        TestCase,
        pk=test_case_id,
        question__assessment__created_by=request.user
    )

    question = test_case.question

    if question.question_type != "PROGRAMMING":
        messages.error(
            request,
            "Test cases can only be edited for programming questions."
        )
        return redirect(
            "assessment_detail",
            pk=question.assessment.pk
        )

    if request.method == "POST":
        form = TestCaseForm(request.POST, instance=test_case)

        if form.is_valid():

            new_test_case_marks = form.cleaned_data.get("marks") or 0

            # Calculate marks of all OTHER test cases.
            # The current test case is excluded because its old marks
            # should not be counted while validating the new marks.
            other_test_case_marks = (
                question.test_cases
                .exclude(pk=test_case.pk)
                .aggregate(
                    total=models.Sum("marks")
                )["total"] or 0
            )

            available_marks = (
                question.marks
                - question.ai_evaluation_marks
                - other_test_case_marks
            )

            if new_test_case_marks > available_marks:
                messages.error(
                    request,
                    (
                        f"Cannot update Test Case {test_case.order}. "
                        f"You are assigning {new_test_case_marks} marks, "
                        f"but only {max(available_marks, 0)} marks are available "
                        f"for this test case. "
                        f"Question marks: {question.marks}, "
                        f"AI evaluation marks: {question.ai_evaluation_marks}, "
                        f"Other test case marks: {other_test_case_marks}."
                    )
                )

            else:
                test_case = form.save()

                messages.success(
                    request,
                    f"Test Case {test_case.order} updated successfully."
                )

                return redirect(
                    "test_case_create",
                    question_id=question.pk
                )

    else:
        form = TestCaseForm(instance=test_case)

    return render(
        request,
        "assessment/test_case_form.html",
        {
            "form": form,
            "question": question,
            "assessment": question.assessment,
            "public_test_cases": question.test_cases.filter(
                is_hidden=False
            ),
            "hidden_test_cases": question.test_cases.filter(
                is_hidden=True
            ),
        }
    )

# ==========================================================
# DELETE TEST CASE
# ==========================================================

@login_required
def test_case_delete(request, test_case_id):

    test_case = get_object_or_404(
        TestCase,
        pk=test_case_id,
        question__assessment__created_by=request.user
    )

    question = test_case.question

    if request.method == "POST":

        test_case.delete()

        messages.success(
            request,
            "Test case deleted successfully."
        )

        return redirect(
            "test_case_create",
            question_id=question.pk
        )

    return render(
        request,
        "assessment/test_case_confirm_delete.html",
        {
            "test_case": test_case,
            "question": question,
            "assessment": question.assessment,
        }
    )


# ==========================================================
# OPTION CREATE
# ==========================================================

@login_required
def option_create(request, question_id):

    question = get_object_or_404(
        AssessmentQuestion,
        pk=question_id,
        assessment__created_by=request.user
    )

    if question.question_type not in [
        "MCQ",
        "MULTIPLE_SELECT"
    ]:

        messages.error(
            request,
            "Options are only available for MCQ and Multiple Select questions."
        )

        return redirect(
            "assessment_detail",
            pk=question.assessment.pk
        )

    if request.method == "POST":

        form = QuestionOptionForm(
            request.POST
        )

        if form.is_valid():

            option = form.save(
                commit=False
            )

            option.question = question

            option.order = (
                question.options.count() + 1
            )

            option.save()

            messages.success(
                request,
                "Option added successfully."
            )

            return redirect(
                "question_options",
                question_id=question.pk
            )

    else:

        form = QuestionOptionForm()

    options = question.options.all()

    return render(
        request,
        "assessment/question_options.html",
        {
            "form": form,
            "question": question,
            "assessment": question.assessment,
            "options": options,
        }
    )


# ==========================================================
# OPTION EDIT
# ==========================================================

@login_required
def option_edit(request, option_id):

    option = get_object_or_404(
        QuestionOption,
        pk=option_id,
        question__assessment__created_by=request.user
    )

    question = option.question

    if request.method == "POST":

        form = QuestionOptionForm(
            request.POST,
            instance=option
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Option updated successfully."
            )

            return redirect(
                "question_options",
                question_id=question.pk
            )

    else:

        form = QuestionOptionForm(
            instance=option
        )

    return render(
        request,
        "assessment/option_edit.html",
        {
            "form": form,
            "option": option,
            "question": question,
            "assessment": question.assessment,
        }
    )


# ==========================================================
# OPTION DELETE
# ==========================================================

@login_required
def option_delete(request, option_id):

    option = get_object_or_404(
        QuestionOption,
        pk=option_id,
        question__assessment__created_by=request.user
    )

    question = option.question

    if request.method == "POST":

        option.delete()

        messages.success(
            request,
            "Option deleted successfully."
        )

        return redirect(
            "question_options",
            question_id=question.pk
        )

    return render(
        request,
        "assessment/option_confirm_delete.html",
        {
            "option": option,
            "question": question,
            "assessment": question.assessment,
        }
    )


# ==========================================================
# CREATE ASSESSMENT PLACEMENT
# ==========================================================

@login_required
def placement_create(request, assessment_id):

    assessment = get_object_or_404(
        Assessment,
        pk=assessment_id,
        created_by=request.user
    )

    if request.method == "POST":

        form = AssessmentPlacementForm(
            request.POST
        )

        if form.is_valid():

            placement = form.save(
                commit=False
            )

            placement.assessment = assessment

            placement.save()

            messages.success(
                request,
                "Assessment placement added successfully."
            )

            return redirect(
                "assessment_detail",
                pk=assessment.pk
            )

    else:

        form = AssessmentPlacementForm()

    return render(
        request,
        "assessment/placement_form.html",
        {
            "form": form,
            "assessment": assessment,
            "is_edit": False,
        }
    )

# ==========================================================
# EDIT ASSESSMENT PLACEMENT
# ==========================================================

@login_required
def placement_edit(request, placement_id):

    placement = get_object_or_404(
        AssessmentPlacement,
        pk=placement_id,
        assessment__created_by=request.user
    )

    assessment = placement.assessment

    if request.method == "POST":

        form = AssessmentPlacementForm(
            request.POST,
            instance=placement
        )

        if form.is_valid():

            form.save()

            messages.success(
                request,
                "Assessment placement updated successfully."
            )

            return redirect(
                "assessment_detail",
                pk=assessment.pk
            )

    else:

        form = AssessmentPlacementForm(
            instance=placement
        )

    return render(
        request,
        "assessment/placement_form.html",
        {
            "form": form,
            "assessment": assessment,
            "placement": placement,
            "is_edit": True,
        }
    )


# ==========================================================
# DELETE ASSESSMENT PLACEMENT
# ==========================================================

@login_required
def placement_delete(request, placement_id):

    placement = get_object_or_404(
        AssessmentPlacement,
        pk=placement_id,
        assessment__created_by=request.user
    )

    assessment = placement.assessment

    if request.method == "POST":

        placement.delete()

        messages.success(
            request,
            "Assessment placement deleted successfully."
        )

        return redirect(
            "assessment_detail",
            pk=assessment.pk
        )

    return render(
        request,
        "assessment/placement_confirm_delete.html",
        {
            "placement": placement,
            "assessment": assessment,
        }
    )


# ==========================================================
# STUDENT ASSESSMENT INSTRUCTIONS
# ==========================================================

@login_required
def student_assessment_list(request):

    assessments = Assessment.objects.filter(
        status="PUBLISHED"
    ).order_by("-created_at")

    return render(
        request,
        "assessment/student_assessment_list.html",
        {
            "assessments": assessments,
        }
    )


@login_required
def student_assessment_start(request, pk):

    assessment = get_object_or_404(
        Assessment,
        pk=pk,
        status="PUBLISHED"
    )

    submissions = AssessmentSubmission.objects.filter(
        assessment=assessment,
        student=request.user
    )

    attempt_count = submissions.count()

    in_progress_attempt = submissions.filter(
        status="IN_PROGRESS"
    ).first()

    attempts_remaining = max(
        assessment.max_attempts - attempt_count,
        0
    )

    return render(
        request,
        "assessment/student_assessment_start.html",
        {
            "assessment": assessment,
            "attempt_count": attempt_count,
            "attempts_remaining": attempts_remaining,
            "in_progress_attempt": in_progress_attempt,
        }
    )


@login_required
def student_assessment_attempt(request, pk):

    assessment = get_object_or_404(
        Assessment,
        pk=pk,
        status="PUBLISHED"
    )

    # ======================================================
    # CHECK EXISTING IN-PROGRESS ATTEMPT
    # ======================================================

    submission = AssessmentSubmission.objects.filter(
        assessment=assessment,
        student=request.user,
        status="IN_PROGRESS"
    ).first()

    # ======================================================
    # CREATE NEW ATTEMPT
    # ======================================================

    if not submission:

        attempt_count = AssessmentSubmission.objects.filter(
            assessment=assessment,
            student=request.user
        ).count()

        if attempt_count >= assessment.max_attempts:

            messages.error(
                request,
                "You have no attempts remaining."
            )

            return redirect(
                "student_assessment_start",
                pk=assessment.pk
            )

        submission = AssessmentSubmission.objects.create(
            assessment=assessment,
            student=request.user,
            attempt_number=attempt_count + 1,
            status="IN_PROGRESS"
        )

    # ======================================================
    # GET ALL QUESTIONS
    # ======================================================

    questions = (
        assessment.questions
        .all()
        .order_by("order")
    )

    # ======================================================
    # GET SELECTED QUESTION
    # ======================================================

    selected_question_id = request.GET.get("question")

    selected_question = None

    if selected_question_id:

        try:

            selected_question = questions.filter(
                pk=int(selected_question_id)
            ).first()

        except (TypeError, ValueError):

            selected_question = None

    # ======================================================
    # DEFAULT QUESTION
    # ======================================================

    if selected_question is None and questions.exists():

        selected_question = questions.first()

    # ======================================================
    # EXISTING ANSWERS
    # ======================================================

    existing_answers = {
        item.question_id: item
        for item in submission.question_submissions.all()
    }


    print("===== SAVED ANSWERS =====")

    for question_id, answer in existing_answers.items():

        print(
            "Question:",
            question_id,
            "Answer:",
            repr(answer.answer_text),
            "Code:",
            repr(answer.submitted_code)
        )

    print("=========================")

    

    # Attach existing submission to every question.

    for question in questions:

        question.existing_submission = (
            existing_answers.get(question.id)
        )

    # ======================================================
    # SELECTED QUESTION SAVED ANSWER
    # ======================================================

    # ======================================================
    # SELECTED QUESTION SAVED ANSWER
    # ======================================================

    selected_answer = None
    selected_multiple_answers = []

    if selected_question:

        saved_submission = existing_answers.get(
            selected_question.id
        )

        if saved_submission:

            if selected_question.question_type == "PROGRAMMING":

                selected_answer = (
                    saved_submission.submitted_code or ""
                )

            elif selected_question.question_type == "MULTIPLE_SELECT":

                try:

                    selected_multiple_answers = json.loads(
                        saved_submission.answer_text or "[]"
                    )

                except (
                    TypeError,
                    ValueError,
                    json.JSONDecodeError
                ):

                    selected_multiple_answers = []

            else:

                selected_answer = (
                    saved_submission.answer_text or ""
                )

    # ======================================================
    # SAVE CURRENT QUESTION / SUBMIT
    # ======================================================

    if request.method == "POST":

        # ==================================================
        # GET CURRENT QUESTION
        # ==================================================

        current_question_id = request.POST.get(
            "current_question"
        )

        current_question = None

        if current_question_id:

            try:

                current_question = questions.filter(
                    pk=int(current_question_id)
                ).first()

            except (TypeError, ValueError):

                current_question = None

        # ==================================================
        # SAVE ONLY CURRENT QUESTION
        # ==================================================

        if current_question:

            field_name = f"question_{current_question.id}"

            if current_question.question_type == "MULTIPLE_SELECT":

                selected_options = request.POST.getlist(
                    field_name
                )

                answer_value = json.dumps(
                    selected_options
                )

                QuestionSubmission.objects.update_or_create(
                    submission=submission,
                    question=current_question,
                    defaults={
                        "answer_text": answer_value,
                    }
                )

            elif current_question.question_type == "PROGRAMMING":

                submitted_code = request.POST.get(
                    field_name,
                    ""
                )

                QuestionSubmission.objects.update_or_create(
                    submission=submission,
                    question=current_question,
                    defaults={
                        "submitted_code": submitted_code,
                    }
                )

            else:

                answer = request.POST.get(
                    field_name,
                    ""
                )

                QuestionSubmission.objects.update_or_create(
                    submission=submission,
                    question=current_question,
                    defaults={
                        "answer_text": answer,
                    }
                )

        # ==================================================
        # SAVE / NEXT / PREVIOUS
        # ==================================================

        if request.POST.get("action") == "save":

            # The POST URL contains the question we want
            # to display after saving.

            target_question_id = request.GET.get(
                "question"
            )

            messages.success(
                request,
                "Your answer has been saved."
            )

            if target_question_id:

                return redirect(
                    f"{reverse('student_assessment_attempt', kwargs={'pk': assessment.pk})}"
                    f"?question={target_question_id}"
                )

            return redirect(
                "student_assessment_attempt",
                pk=assessment.pk
            )

        # ==================================================
        # FINAL SUBMIT
        # ==================================================

        if request.POST.get("action") == "submit":

            evaluate_submission(
                submission
            )

            submission.status = "EVALUATED"

            submission.submitted_at = timezone.now()

            submission.save(
                update_fields=[
                    "status",
                    "submitted_at",
                    "total_marks",
                ]
            )

            messages.success(
                request,
                "Assessment submitted successfully."
            )

            return redirect(
                "student_assessment_result",
                pk=submission.pk
            )

    # ======================================================
    # REFRESH EXISTING ANSWERS
    # ======================================================
    existing_answers = {
        item.question_id: item
        for item in submission.question_submissions.all()
    }

    # ======================================================
    # DETERMINE ACTUALLY ANSWERED QUESTIONS
    # ======================================================

    answered_question_ids = set()

    for question_id, answer in existing_answers.items():

        if answer.question.question_type == "PROGRAMMING":

            if answer.submitted_code and answer.submitted_code.strip():
                answered_question_ids.add(question_id)

        elif answer.question.question_type == "MULTIPLE_SELECT":

            try:
                selected_options = json.loads(
                    answer.answer_text or "[]"
                )

                if selected_options:
                    answered_question_ids.add(question_id)

            except (TypeError, ValueError, json.JSONDecodeError):

                pass

        else:

            if answer.answer_text and answer.answer_text.strip():
                answered_question_ids.add(question_id)

    # ======================================================
    # FIND CURRENT QUESTION POSITION
    # ======================================================

    current_question_index = 0

    if selected_question:

        for index, question in enumerate(questions):

            if question.id == selected_question.id:

                current_question_index = index

                break

    # ======================================================
    # PREVIOUS / NEXT QUESTION
    # ======================================================

    previous_question = None
    next_question = None

    if current_question_index > 0:

        previous_question = questions[
            current_question_index - 1
        ]

    if current_question_index < questions.count() - 1:

        next_question = questions[
            current_question_index + 1
        ]

    # ======================================================
    # RENDER
    # ======================================================

    return render(
        request,
        "assessment/student_assessment_attempt.html",
        {
            "assessment": assessment,
            "questions": questions,
            "selected_question": selected_question,
            "submission": submission,
            "existing_answers": existing_answers,
            "current_question_index": current_question_index,
            "previous_question": previous_question,
            "next_question": next_question,
            "answered_question_ids": answered_question_ids,
            "selected_answer": selected_answer,
            "selected_multiple_answers": selected_multiple_answers,
        }
    )

# ==========================================================
# AUTO-SAVE STUDENT ANSWER
# ==========================================================

@login_required
def autosave_assessment_answer(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "error": "Only POST requests are allowed.",
            },
            status=405,
        )

    # ======================================================
    # READ REQUEST DATA
    # ======================================================

    try:
        data = json.loads(request.body)

    except (json.JSONDecodeError, TypeError):
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid request data.",
            },
            status=400,
        )

    assessment_id = data.get("assessment_id")
    question_id = data.get("question_id")
    answer = data.get("answer", "")

    # ======================================================
    # VALIDATE REQUIRED DATA
    # ======================================================

    if not assessment_id or not question_id:
        return JsonResponse(
            {
                "success": False,
                "error": "Assessment and question are required.",
            },
            status=400,
        )

    # ======================================================
    # GET ASSESSMENT
    # ======================================================

    assessment = get_object_or_404(
        Assessment,
        pk=assessment_id,
        status="PUBLISHED",
    )

    # ======================================================
    # GET CURRENT IN-PROGRESS SUBMISSION
    # ======================================================

    submission = AssessmentSubmission.objects.filter(
        assessment=assessment,
        student=request.user,
        status="IN_PROGRESS",
    ).first()

    if not submission:
        return JsonResponse(
            {
                "success": False,
                "error": "No active assessment attempt found.",
            },
            status=400,
        )

    # ======================================================
    # GET QUESTION
    # ======================================================

    question = get_object_or_404(
        AssessmentQuestion,
        pk=question_id,
        assessment=assessment,
    )

    # ======================================================
    # SAVE ANSWER
    # ======================================================

    if question.question_type == "MULTIPLE_SELECT":

        if not isinstance(answer, list):
            answer = []

        answer_value = json.dumps(
            [str(option_id) for option_id in answer]
        )

        QuestionSubmission.objects.update_or_create(
            submission=submission,
            question=question,
            defaults={
                "answer_text": answer_value,
            },
        )

    elif question.question_type == "PROGRAMMING":

        QuestionSubmission.objects.update_or_create(
            submission=submission,
            question=question,
            defaults={
                "submitted_code": str(answer),
            },
        )

    else:

        QuestionSubmission.objects.update_or_create(
            submission=submission,
            question=question,
            defaults={
                "answer_text": str(answer),
            },
        )

    # ======================================================
    # RESPONSE
    # ======================================================

    return JsonResponse(
        {
            "success": True,
            "message": "Answer saved.",
            "question_id": question.id,
        }
    )


def normalize_answer(value):

    if value is None:
        return ""

    return " ".join(
        str(value)
        .strip()
        .lower()
        .split()
    )


def evaluate_submission(submission):

    total_marks = 0

    questions = (
        submission.assessment.questions
        .all()
        .order_by("order")
    )

    for question in questions:

        question_submission = (
            submission.question_submissions
            .filter(
                question=question
            )
            .first()
        )

        # --------------------------------------------------
        # NO ANSWER
        # --------------------------------------------------

        if not question_submission:

            continue

        awarded_marks = 0

        is_correct = False

        feedback = ""

        # ==================================================
        # MCQ
        # ==================================================

        if question.question_type == "MCQ":

            selected_option = (
                question_submission.answer_text
            )

            correct_option = (
                question.options
                .filter(is_correct=True)
                .first()
            )

            if (
                correct_option
                and selected_option
                == str(correct_option.id)
            ):

                awarded_marks = question.marks

                is_correct = True

                feedback = "Correct answer."

            else:

                feedback = "Incorrect answer."

        # ==================================================
        # MULTIPLE SELECT
        # ==================================================

        elif question.question_type == "MULTIPLE_SELECT":

            try:

                selected_options = set(
                    json.loads(
                        question_submission.answer_text
                        or "[]"
                    )
                )

            except (
                json.JSONDecodeError,
                TypeError
            ):

                selected_options = set()

            correct_options = set(
                str(option.id)
                for option in question.options.filter(
                    is_correct=True
                )
            )

            if (
                selected_options
                == correct_options
            ):

                awarded_marks = question.marks

                is_correct = True

                feedback = (
                    "All correct options selected."
                )

            else:

                feedback = (
                    "Incorrect selection."
                )

        # ==================================================
        # FILL BLANK
        # ==================================================

        elif question.question_type == "FILL_BLANK":

            student_answer = (
                question_submission.answer_text or ""
            )

            accepted_answers = []

            if isinstance(
                question.evaluation_criteria,
                dict
            ):
                accepted_answers = (
                    question.evaluation_criteria.get(
                        "accepted_answers",
                        []
                    )
                )

            # Fallback to reference_answer if no
            # accepted answers are configured.
            if not accepted_answers and question.reference_answer:
                accepted_answers = [
                    question.reference_answer
                ]

            student_normalized = normalize_answer(
                student_answer
            )

            answer_matched = any(
                student_normalized
                ==
                normalize_answer(accepted_answer)
                for accepted_answer in accepted_answers
            )

            if answer_matched:

                awarded_marks = question.marks

                is_correct = True

                feedback = "Correct answer."

            else:

                feedback = "Incorrect answer."

        # ==================================================
        # THEORY
        # ==================================================

        elif question.question_type == "THEORY":

            theory_result = evaluate_theory_answer(
                question_text=question.question_text,
                student_answer=(
                    question_submission.answer_text or ""
                ),
                max_marks=question.marks,
                reference_answer=question.reference_answer,
                evaluation_criteria=question.evaluation_criteria,
            )

            awarded_marks = theory_result["marks"]

            is_correct = theory_result["is_correct"]

            feedback = theory_result["feedback"]

        # ==================================================
        # PROGRAMMING
        # ==================================================

        elif question.question_type == "PROGRAMMING":

            if question_submission.submitted_code:

                # --------------------------------------------------
                # FUNCTIONAL / TEST CASE EVALUATION
                # --------------------------------------------------

                evaluation = (
                    evaluate_programming_question(
                        question=question,
                        submitted_code=(
                            question_submission.submitted_code
                        ),
                    )
                )

                test_case_marks = evaluation["marks"]

                is_correct = (
                    evaluation["status"]
                    == "PASSED"
                )

                functional_feedback = (
                    evaluation["feedback"]
                )

                # --------------------------------------------------
                # AI CODE QUALITY EVALUATION
                # --------------------------------------------------

                code_quality_result = (
                    evaluate_code_quality(
                        question_text=question.question_text,
                        submitted_code=(
                            question_submission.submitted_code
                        ),
                        language=question.language,
                        max_marks=question.ai_evaluation_marks,
                        reference_answer=question.reference_answer,
                    )
                )

                ai_quality_marks = (
                    code_quality_result["marks"]
                )

                code_quality_feedback = (
                    code_quality_result["feedback"]
                )

                # --------------------------------------------------
                # FINAL PROGRAMMING MARKS
                # --------------------------------------------------

                awarded_marks = (
                    test_case_marks
                    + ai_quality_marks
                )

                # Safety limit
                awarded_marks = min(
                    awarded_marks,
                    question.marks
                )

                # --------------------------------------------------
                # COMBINED FEEDBACK
                # --------------------------------------------------

                feedback = (
                    f"Test Case Evaluation: "
                    f"{functional_feedback}\n\n"
                    f"Code Quality Evaluation: "
                    f"{code_quality_feedback}"
                )

            else:

                awarded_marks = 0

                feedback = (
                    "No code submitted."
                )

                is_correct = False

        # ==================================================
        # SAVE QUESTION RESULT
        # ==================================================

        question_submission.marks_awarded = (
            awarded_marks
        )

        question_submission.is_correct = (
            is_correct
        )

        question_submission.feedback = (
            feedback
        )

        question_submission.evaluated_at = (
            timezone.now()
        )

        question_submission.save()

        total_marks += awarded_marks

    # ======================================================
    # SAVE TOTAL
    # ======================================================

    submission.total_marks = total_marks

    return total_marks


# ==========================================================
# RUN CODE - STUDENT TESTING
# ==========================================================

# @login_required
# def run_code(request):

#     if request.method != "POST":
#         return JsonResponse(
#             {
#                 "success": False,
#                 "status": "INVALID_METHOD",
#                 "error": "Only POST requests are allowed.",
#             },
#             status=405,
#         )

#     # ======================================================
#     # READ REQUEST
#     # ======================================================

#     try:

#         data = json.loads(request.body)

#     except (json.JSONDecodeError, TypeError):

#         return JsonResponse(
#             {
#                 "success": False,
#                 "status": "INVALID_REQUEST",
#                 "error": "Invalid request data.",
#             },
#             status=400,
#         )

#     code = data.get("code", "")
#     language = data.get("language", "")
#     input_data = data.get("input", "")
#     question_id = data.get("question_id")

#     # ======================================================
#     # VALIDATE CODE
#     # ======================================================

#     if not code or not code.strip():

#         return JsonResponse(
#             {
#                 "success": False,
#                 "status": "NO_CODE",
#                 "error": "Please write some code first.",
#             }
#         )

#     # ======================================================
#     # VALIDATE QUESTION
#     # ======================================================

#     if not question_id:

#         return JsonResponse(
#             {
#                 "success": False,
#                 "status": "NO_QUESTION",
#                 "error": "Programming question was not specified.",
#             }
#         )

#     question = get_object_or_404(
#         AssessmentQuestion,
#         pk=question_id,
#         question_type="PROGRAMMING",
#     )

#     # ======================================================
#     # VALIDATE LANGUAGE
#     # ======================================================

#     if question.language != language:

#         return JsonResponse(
#             {
#                 "success": False,
#                 "status": "LANGUAGE_MISMATCH",
#                 "error": "Invalid programming language.",
#             }
#         )

#     # ======================================================
#     # GET RUNNER
#     # ======================================================

#     try:

#         runner = get_runner(language)

#     except ValueError as error:

#         return JsonResponse(
#             {
#                 "success": False,
#                 "status": "CONFIGURATION_ERROR",
#                 "error": str(error),
#             }
#         )

#     # ======================================================
#     # RUN CODE WITH CUSTOM INPUT ONLY
#     # ======================================================

#     try:

#         result = runner.run(
#             code=code,
#             input_data=input_data or "",
#         )

#     except Exception as error:

#         return JsonResponse(
#             {
#                 "success": False,
#                 "status": "ERROR",
#                 "error": str(error),
#             }
#         )

#     # ======================================================
#     # BUILD RESPONSE
#     # ======================================================

#     return JsonResponse(
#         {
#             "success": True,

#             "custom": {
#                 "success": result.success,
#                 "status": result.status,
#                 "output": result.output,
#                 "error": result.error,
#                 "timed_out": result.timed_out,
#                 "compile_error": result.compile_error,
#                 "execution_time": round(
#                     result.execution_time,
#                     3
#                 ),
#             },

#             # IMPORTANT:
#             # Run Code does NOT execute official
#             # test cases.
#             "tests": {
#                 "passed": 0,
#                 "total": 0,
#                 "all_passed": False,
#                 "results": [],
#             },
#         }
#     )


# ==========================================================
# RUN & CHECK - PROGRAMMING QUESTION
# ==========================================================

@login_required
def check_programming_code(request):

    if request.method != "POST":
        return JsonResponse(
            {
                "success": False,
                "status": "INVALID_METHOD",
                "error": "Only POST requests are allowed.",
            },
            status=405,
        )

    # ======================================================
    # READ REQUEST
    # ======================================================

    try:
        data = json.loads(request.body)

    except (json.JSONDecodeError, TypeError):

        return JsonResponse(
            {
                "success": False,
                "status": "INVALID_REQUEST",
                "error": "Invalid request data.",
            },
            status=400,
        )

    code = data.get("code", "")
    language = data.get("language", "")
    question_id = data.get("question_id")

    # ======================================================
    # VALIDATE CODE
    # ======================================================

    if not code or not code.strip():

        return JsonResponse(
            {
                "success": False,
                "status": "NO_CODE",
                "error": "Please write some code first.",
            }
        )

    # ======================================================
    # VALIDATE QUESTION
    # ======================================================

    if not question_id:

        return JsonResponse(
            {
                "success": False,
                "status": "NO_QUESTION",
                "error": "Programming question was not specified.",
            }
        )

    question = get_object_or_404(
        AssessmentQuestion,
        pk=question_id,
        question_type="PROGRAMMING",
    )

    # ======================================================
    # VALIDATE LANGUAGE
    # ======================================================

    if question.language != language:

        return JsonResponse(
            {
                "success": False,
                "status": "LANGUAGE_MISMATCH",
                "error": "Invalid programming language.",
            }
        )

    # ======================================================
    # EVALUATE AGAINST OFFICIAL TEST CASES
    # ======================================================

    try:

        evaluation = evaluate_programming_question(
            question=question,
            submitted_code=code,
        )

        print("===== RUN & CHECK EVALUATION =====")
        print(evaluation)
        print("==================================")

    except Exception as error:

        return JsonResponse(
            {
                "success": False,
                "status": "EVALUATION_ERROR",
                "error": str(error),
            },
            status=500,
        )

    # ======================================================
    # BUILD SAFE TEST RESULTS
    # ======================================================

    test_results = []

    for result in evaluation["test_results"]:

        test_result = {
            "test_case_id": result["test_case_id"],
            "order": result["order"],
            "passed": result["passed"],
            "status": result["status"],
            "marks": result["marks"],
            "max_marks": result["max_marks"],
            "execution_time": result["execution_time"],
            "feedback": result["feedback"],
            "is_hidden": result["is_hidden"],
        }

        # --------------------------------------------------
        # PUBLIC TEST CASE
        # --------------------------------------------------

        if not result["is_hidden"]:

            test_result["actual_output"] = (
                result["actual_output"]
            )

            test_result["expected_output"] = (
                result["expected_output"]
            )

        # --------------------------------------------------
        # HIDDEN TEST CASE
        # --------------------------------------------------
        # IMPORTANT:
        # Do NOT send input, expected output, or actual
        # output for hidden test cases.

        else:

            test_result["actual_output"] = None
            test_result["expected_output"] = None

        test_results.append(test_result)

    # ======================================================
    # RESPONSE
    # ======================================================

    return JsonResponse(
        {
            "success": True,
            "status": evaluation["status"],
            "marks": evaluation["marks"],
            "max_marks": evaluation["max_marks"],
            "passed": evaluation["passed"],
            "total_tests": evaluation["total_tests"],
            "feedback": evaluation["feedback"],
            "test_results": test_results,
        }
    )


# ==========================================================
# INTERACTIVE CODE - START
# ==========================================================

@login_required
def interactive_code_start(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "status": "INVALID_METHOD",
                "error": "Only POST requests are allowed.",
            },
            status=405,
        )

    # ------------------------------------------------------
    # CLEAN OLD SESSIONS
    # ------------------------------------------------------

    cleanup_expired_interactive_sessions()

    # ------------------------------------------------------
    # READ REQUEST
    # ------------------------------------------------------

    try:

        data = json.loads(request.body)

    except (json.JSONDecodeError, TypeError):

        return JsonResponse(
            {
                "success": False,
                "status": "INVALID_REQUEST",
                "error": "Invalid request data.",
            },
            status=400,
        )

    code = data.get("code", "")
    language = data.get("language", "")
    question_id = data.get("question_id")

    # ------------------------------------------------------
    # VALIDATE CODE
    # ------------------------------------------------------

    if not code or not code.strip():

        return JsonResponse(
            {
                "success": False,
                "status": "NO_CODE",
                "error": "Please write some code first.",
            }
        )

    # ------------------------------------------------------
    # VALIDATE QUESTION
    # ------------------------------------------------------

    if not question_id:

        return JsonResponse(
            {
                "success": False,
                "status": "NO_QUESTION",
                "error": "Programming question was not specified.",
            }
        )

    question = get_object_or_404(
        AssessmentQuestion,
        pk=question_id,
        question_type="PROGRAMMING",
    )

    # ------------------------------------------------------
    # VALIDATE LANGUAGE
    # ------------------------------------------------------

    if question.language != language:

        return JsonResponse(
            {
                "success": False,
                "status": "LANGUAGE_MISMATCH",
                "error": "Invalid programming language.",
            }
        )

    # ------------------------------------------------------
    # START INTERACTIVE PROCESS
    # ------------------------------------------------------

    try:

        session = interactive_runner.start(
            code=code,
            language=language,
        )

    except ValueError as error:

        return JsonResponse(
            {
                "success": False,
                "status": "CONFIGURATION_ERROR",
                "error": str(error),
            }
        )

    except Exception as error:

        return JsonResponse(
            {
                "success": False,
                "status": "START_ERROR",
                "error": str(error),
            }
        )

    # ------------------------------------------------------
    # STORE SESSION
    # ------------------------------------------------------

    with interactive_sessions_lock:

        interactive_sessions[
            session.session_id
        ] = {
            "session": session,
            "user_id": request.user.id,
            "question_id": question.id,
            "created_at": time.time(),
        }

    # ------------------------------------------------------
    # READ IMMEDIATE OUTPUT
    # ------------------------------------------------------

    time.sleep(0.05)

    output = session.read_output()

    # ------------------------------------------------------
    # RESPONSE
    # ------------------------------------------------------

    return JsonResponse(
        {
            "success": True,
            "status": "STARTED",
            "session_id": session.session_id,
            "output": output,
            "running": session.is_running(),
        }
    )


# ==========================================================
# INTERACTIVE CODE - READ OUTPUT
# ==========================================================

@login_required
def interactive_code_read(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "status": "INVALID_METHOD",
                "error": "Only POST requests are allowed.",
            },
            status=405,
        )

    try:

        data = json.loads(request.body)

    except (json.JSONDecodeError, TypeError):

        return JsonResponse(
            {
                "success": False,
                "status": "INVALID_REQUEST",
                "error": "Invalid request data.",
            },
            status=400,
        )

    session_id = data.get("session_id")

    if not session_id:

        return JsonResponse(
            {
                "success": False,
                "status": "NO_SESSION",
                "error": "Interactive session was not specified.",
            }
        )

    with interactive_sessions_lock:

        session_data = interactive_sessions.get(
            session_id
        )

    if not session_data:

        return JsonResponse(
            {
                "success": False,
                "status": "SESSION_NOT_FOUND",
                "error": "Interactive session was not found.",
            }
        )

    # ------------------------------------------------------
    # SECURITY
    # ------------------------------------------------------

    if session_data["user_id"] != request.user.id:

        return JsonResponse(
            {
                "success": False,
                "status": "FORBIDDEN",
                "error": "You do not have access to this session.",
            },
            status=403,
        )

    session = session_data["session"]

    # ------------------------------------------------------
    # EXPIRED SESSION
    # ------------------------------------------------------

    if session.is_expired():

        stop_interactive_session(
            session_id
        )

        return JsonResponse(
            {
                "success": False,
                "status": "SESSION_EXPIRED",
                "error": "Interactive session expired.",
            }
        )

    # ------------------------------------------------------
    # READ OUTPUT
    # ------------------------------------------------------

    output = session.read_output()

    running = session.is_running()

    # ------------------------------------------------------
    # REMOVE FINISHED SESSION
    # ------------------------------------------------------

    if not running:

        # Read anything that arrived just before
        # the process terminated.

        output += session.read_output()

        stop_interactive_session(
            session_id
        )

    return JsonResponse(
        {
            "success": True,
            "status": "RUNNING" if running else "FINISHED",
            "output": output,
            "running": running,
        }
    )


# ==========================================================
# INTERACTIVE CODE - SEND INPUT
# ==========================================================

@login_required
def interactive_code_input(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "status": "INVALID_METHOD",
                "error": "Only POST requests are allowed.",
            },
            status=405,
        )

    try:

        data = json.loads(request.body)

    except (json.JSONDecodeError, TypeError):

        return JsonResponse(
            {
                "success": False,
                "status": "INVALID_REQUEST",
                "error": "Invalid request data.",
            },
            status=400,
        )

    session_id = data.get("session_id")
    input_data = data.get("input", "")

    if not session_id:

        return JsonResponse(
            {
                "success": False,
                "status": "NO_SESSION",
                "error": "Interactive session was not specified.",
            }
        )

    with interactive_sessions_lock:

        session_data = interactive_sessions.get(
            session_id
        )

    if not session_data:

        return JsonResponse(
            {
                "success": False,
                "status": "SESSION_NOT_FOUND",
                "error": "Interactive session was not found.",
            }
        )

    # ------------------------------------------------------
    # SECURITY
    # ------------------------------------------------------

    if session_data["user_id"] != request.user.id:

        return JsonResponse(
            {
                "success": False,
                "status": "FORBIDDEN",
                "error": "You do not have access to this session.",
            },
            status=403,
        )

    session = session_data["session"]

    # ------------------------------------------------------
    # EXPIRED SESSION
    # ------------------------------------------------------

    if session.is_expired():

        stop_interactive_session(
            session_id
        )

        return JsonResponse(
            {
                "success": False,
                "status": "SESSION_EXPIRED",
                "error": "Interactive session expired.",
            }
        )

    # ------------------------------------------------------
    # SEND INPUT
    # ------------------------------------------------------

    success, error = session.send_input(
        str(input_data)
    )

    if not success:

        return JsonResponse(
            {
                "success": False,
                "status": "INPUT_ERROR",
                "error": error,
            }
        )

    return JsonResponse(
        {
            "success": True,
            "status": "INPUT_SENT",
        }
    )


# ==========================================================
# INTERACTIVE CODE - STOP
# ==========================================================

@login_required
def interactive_code_stop(request):

    if request.method != "POST":

        return JsonResponse(
            {
                "success": False,
                "status": "INVALID_METHOD",
                "error": "Only POST requests are allowed.",
            },
            status=405,
        )

    try:

        data = json.loads(request.body)

    except (json.JSONDecodeError, TypeError):

        return JsonResponse(
            {
                "success": False,
                "status": "INVALID_REQUEST",
                "error": "Invalid request data.",
            },
            status=400,
        )

    session_id = data.get("session_id")

    if not session_id:

        return JsonResponse(
            {
                "success": False,
                "status": "NO_SESSION",
                "error": "Interactive session was not specified.",
            }
        )

    with interactive_sessions_lock:

        session_data = interactive_sessions.get(
            session_id
        )

    if not session_data:

        return JsonResponse(
            {
                "success": True,
                "status": "ALREADY_STOPPED",
            }
        )

    # ------------------------------------------------------
    # SECURITY
    # ------------------------------------------------------

    if session_data["user_id"] != request.user.id:

        return JsonResponse(
            {
                "success": False,
                "status": "FORBIDDEN",
                "error": "You do not have access to this session.",
            },
            status=403,
        )

    # ------------------------------------------------------
    # STOP
    # ------------------------------------------------------

    stop_interactive_session(
        session_id
    )

    return JsonResponse(
        {
            "success": True,
            "status": "STOPPED",
        }
    )



# ==========================================================
# STUDENT ASSESSMENT RESULT
# ==========================================================

@login_required
def student_assessment_result(request, pk):

    submission = get_object_or_404(
        AssessmentSubmission,
        pk=pk,
        student=request.user
    )

    questions = (
        submission.question_submissions
        .select_related("question")
        .order_by("question__order")
    )

    return render(
        request,
        "assessment/student_assessment_result.html",
        {
            "submission": submission,
            "assessment": submission.assessment,
            "questions": questions,
        }
    )