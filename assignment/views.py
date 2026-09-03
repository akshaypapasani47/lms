from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from programming_lab.models import VirtualLab, VirtualLabAccess
from .models import Assignment, AssignmentQuestion, TestCase, StudentSubmission, QuestionSubmission
from .forms import AssignmentForm, AssignmentQuestionForm, TestCaseForm
from .services import evaluate_submission


def is_lecturer_or_admin(user):
    """Helper to check permissions using existing user fields directly."""
    return user.is_superuser or user.is_lecturer 
@login_required
def assignment_list(request):
    """
    Shows assignments based on user role:
    - Lecturer/Admin: All assignments created or published.
    - Student: Only published assignments for labs they have active access to.
    """
    if is_lecturer_or_admin(request.user):
        assignments = Assignment.objects.all()
    else:
        accessible_labs = VirtualLabAccess.objects.filter(
            student=request.user, 
            is_active=True
        ).values_list("lab_id", flat=True)
        
        assignments = Assignment.objects.filter(
            virtual_lab_id__in=accessible_labs,
            status="PUBLISHED"
        )

    return render(request, "assignment/assignment_list.html", {"assignments": assignments})


@login_required
def create_assignment(request):
    """Lecturer/Admin endpoint to create an assignment."""
    if not is_lecturer_or_admin(request.user):
        messages.error(request, "Unauthorized access. Only Lecturers and Admins can create assignments.")
        return redirect("assignment_list")

    if request.method == "POST":
        form = AssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.created_by = request.user
            assignment.save()
            messages.success(request, f"Assignment '{assignment.title}' created successfully.")
            return redirect("assignment_detail", assignment_id=assignment.id)
    else:
        form = AssignmentForm()

    return render(request, "assignment/create_assignment.html", {"form": form})


@login_required
def assignment_detail(request, assignment_id):
    """Detailed view displaying questions, test cases, and student status."""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    # Check access permission if user is not a lecturer/admin
    if not is_lecturer_or_admin(request.user):
        has_access = VirtualLabAccess.objects.filter(
            lab=assignment.virtual_lab, 
            student=request.user, 
            is_active=True
        ).exists()
        if not has_access:
            messages.error(request, "You do not have access to this lab's assignments.")
            return redirect("assignment_list")

    questions = assignment.questions.all().prefetch_related("test_cases")
    previous_submission = StudentSubmission.objects.filter(
        assignment=assignment, 
        student=request.user
    ).first()

    context = {
        "assignment": assignment,
        "questions": questions,
        "previous_submission": previous_submission,
    }
    return render(request, "assignment/assignment_detail.html", context)


@login_required
def submit_assignment(request, assignment_id):
    """Processes student submissions and triggers evaluation."""
    assignment = get_object_or_404(Assignment, id=assignment_id)

    if request.method == "POST":
        submission, _ = StudentSubmission.objects.get_or_create(
            assignment=assignment,
            student=request.user
        )

        for question in assignment.questions.all():
            code_field_name = f"code_q_{question.id}"
            submitted_code = request.POST.get(code_field_name, "")

            QuestionSubmission.objects.update_or_create(
                submission=submission,
                question=question,
                defaults={"submitted_code": submitted_code}
            )

        evaluate_submission(submission.id)
        messages.success(request, "Assignment submitted and evaluated successfully!")
        return redirect("submission_result", submission_id=submission.id)

    return redirect("assignment_detail", assignment_id=assignment.id)


@login_required
def submission_result(request, submission_id):
    """Displays execution output, test case results, and feedback."""
    submission = get_object_or_404(StudentSubmission, id=submission_id)
    
    if not is_lecturer_or_admin(request.user) and submission.student != request.user:
        messages.error(request, "Unauthorized access to submission results.")
        return redirect("assignment_list")

    answers = submission.question_answers.select_related("question").all()
    context = {
        "submission": submission,
        "answers": answers,
    }
    return render(request, "assignment/submission_result.html", context)


@login_required
def add_question(request, assignment_id):
    """Allows lecturers to add a question to an assignment."""
    assignment = get_object_or_404(Assignment, id=assignment_id)
    if not is_lecturer_or_admin(request.user):
        messages.error(request, "Unauthorized access.")
        return redirect("assignment_list")

    if request.method == "POST":
        form = AssignmentQuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.assignment = assignment
            question.save()
            messages.success(request, f"Question {question.question_number} added.")
            return redirect("add_test_case", question_id=question.id)
    else:
        next_q_num = assignment.questions.count() + 1
        form = AssignmentQuestionForm(initial={"question_number": next_q_num})

    return render(request, "assignment/add_question.html", {"form": form, "assignment": assignment})


@login_required
def add_test_case(request, question_id):
    """Allows lecturers to attach input/output test cases to a question."""
    question = get_object_or_404(AssignmentQuestion, id=question_id)
    if not is_lecturer_or_admin(request.user):
        messages.error(request, "Unauthorized access.")
        return redirect("assignment_list")

    if request.method == "POST":
        form = TestCaseForm(request.POST)
        if form.is_valid():
            test_case = form.save(commit=False)
            test_case.question = question
            test_case.save()
            messages.success(request, "Test Case added successfully.")
            if "add_another" in request.POST:
                return redirect("add_test_case", question_id=question.id)
            return redirect("assignment_detail", assignment_id=question.assignment.id)
    else:
        form = TestCaseForm()

    existing_test_cases = question.test_cases.all()
    context = {
        "form": form,
        "question": question,
        "test_cases": existing_test_cases,
    }
    return render(request, "assignment/add_test_case.html", context)

@login_required
def edit_question(request, question_id):
    """Allows lecturers to edit an existing question."""
    question = get_object_or_404(AssignmentQuestion, id=question_id)
    if not is_lecturer_or_admin(request.user):
        messages.error(request, "Unauthorized access.")
        return redirect("assignment_list")

    if request.method == "POST":
        form = AssignmentQuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, "Question updated successfully.")
            return redirect("assignment_detail", assignment_id=question.assignment.id)
    else:
        form = AssignmentQuestionForm(instance=question)

    return render(request, "assignment/edit_question.html", {"form": form, "question": question})


@login_required
def edit_test_case(request, test_case_id):
    """Allows lecturers to edit an existing test case."""
    test_case = get_object_or_404(TestCase, id=test_case_id)
    if not is_lecturer_or_admin(request.user):
        messages.error(request, "Unauthorized access.")
        return redirect("assignment_list")

    if request.method == "POST":
        form = TestCaseForm(request.POST, instance=test_case)
        if form.is_valid():
            form.save()
            messages.success(request, "Test case updated successfully.")
            return redirect("add_test_case", question_id=test_case.question.id)
    else:
        form = TestCaseForm(instance=test_case)

    return render(request, "assignment/edit_test_case.html", {"form": form, "test_case": test_case})