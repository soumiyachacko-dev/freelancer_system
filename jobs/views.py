from django.shortcuts import render, redirect,get_object_or_404
from .models import Job, Application, UserProfile, Contract, Payment, Task, Clientprofile
from django.db.models import Sum
from django.db.models import Q
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from decimal import Decimal
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.core.paginator import Paginator
from django.conf import settings
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt



def client_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        profile = getattr(request.user, 'userprofile', None)
        if not profile or profile.role != 'client':
            messages.error(request, "You must be a client to access this page.")
            return redirect('index')  # your homepage URL name

        return view_func(request, *args, **kwargs)

    return _wrapped_view
def freelancer_required(view_func):
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):

        profile = getattr(request.user, 'userprofile', None)

        if not profile or profile.role != 'freelancer':
            messages.error(request, "You must be a freelancer to access this page.")
            return redirect('index')  # your homepage URL name

        return view_func(request, *args, **kwargs)

    return _wrapped_view
def index(request):
    from django.contrib.auth.models import User
    from django.http import HttpResponse
    def create_admin(request):
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                'admin',
                'admin@gmail.com',
                'admin123'
            )

        return HttpResponse("Superuser created")



    return render(request, 'index.html')

@client_required
def employer_dashboard(request):
    query = request.GET.get('q')
    jobs_qs = Job.objects.filter(client=request.user) \
        .prefetch_related(
        'applications__user',
        'applications__contract',
        'applications__contract__tasks'
    )
    if query:
        jobs_qs = jobs_qs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )
    paginator = Paginator(jobs_qs.order_by('-created_at'), 2)
    page_number = request.GET.get('page')
    jobs_page = paginator.get_page(page_number)
    job_data = []
    for job in jobs_page:
        applications = job.applications.all()
        app_list = []
        for app in applications:
            contract = Contract.objects.filter(
                job=job,
                freelancer=app.user
            ).first()
            tasks = contract.tasks.all() if contract else None
            has_tasks = tasks.exists() if tasks else False
            is_completed = has_tasks and not tasks.filter(status__in=['pending', 'active']).exists()

            app_list.append({
                'app': app,
                'contract': contract,
                'has_tasks': has_tasks,
                'is_completed': is_completed,
            })
        job_data.append({
            'job': job,
            'applications': app_list
        })
    total_jobs = jobs_qs.count()
    active_contracts = Contract.objects.filter(
        client=request.user,
        status='active',
        tasks__isnull=False).distinct().count()
    total_spent = Payment.objects.filter(
        contract__client=request.user,
        status='paid'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    return render(request, 'employer_dashboard.html', {
        'job_data': job_data,
        'jobs_page': jobs_page,
        'total_jobs': total_jobs,
        'active_contracts': active_contracts,
        'total_spent': total_spent,

    })

@freelancer_required
def freelancer_dashboard(request):
    query = request.GET.get('q')
    jobs_qs = Job.objects.filter(status='open')
    if query:
        jobs_qs = jobs_qs.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )
    paginator = Paginator(jobs_qs.order_by('-created_at'), 2)
    page_number = request.GET.get('page')
    jobs_page = paginator.get_page(page_number)
    contracts = Contract.objects.filter(freelancer=request.user,status='active')
    total_earnings = Payment.objects.filter(
        contract__freelancer=request.user,
        status='paid'
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    completed_tasks = Contract.objects.filter(
    freelancer=request.user,
    status='completed'
).count()
    applied_jobs = Application.objects.filter(
        user=request.user
    ).values_list('job_id', flat=True)
    jobs_with_status = [
        {
            'job': job,
            'applied': job.id in applied_jobs,
        }
        for job in jobs_page
    ]
    return render(request, 'freelancer_dashboard.html', {
        'jobs_with_status': jobs_with_status,
        'contracts': contracts,
        'total_earnings': total_earnings,
        'completed_tasks': completed_tasks,
        'jobs_page': jobs_page,
    })

@client_required
def post_job(request):
    if request.method == "POST":
        title = request.POST['title']
        desc = request.POST['description']
        deadline = request.POST.get('deadline')
        try:
            budget = int(request.POST['budget'])
            if budget <= 0:
                raise ValueError
        except:
            messages.error(request, "Invalid budget")
            return redirect('post_job')
        Job.objects.create(
            title=title,
            description=desc,
            budget=budget,
            client=request.user,
            deadline=deadline,
        )
        return redirect('employer_dashboard')
    return render(request, 'post_job.html')
@freelancer_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, status='open')
    already_applied = Application.objects.filter(
        user=request.user,
        job=job
    ).exists()
    if not already_applied:
        Application.objects.create(
            user=request.user,
            job=job,
            status='pending'
        )
    return redirect('freelancer_dashboard')

@freelancer_required
def my_applications(request):
    applications = Application.objects.filter(
        user=request.user
    ).select_related('job', 'contract')

    return render(request, 'my_applications.html', {
        'applications': applications
    })

def register(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        email = request.POST['email']
        role = request.POST['role']
        # Check username
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('register')
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect('register')
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect('register')
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        UserProfile.objects.create(
            user=user,
            role=role
        )
        if role == 'client':
            Clientprofile.objects.create(user=user)
        return redirect('login')
    return render(request, 'register.html')

def user_login(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            profile = getattr(user, 'userprofile', None)
            if profile and profile.role == 'client':
                return redirect('employer_dashboard')
            elif profile:
                return redirect('freelancer_dashboard')
            else:
                messages.error(request, "Your account has no role assigned. Please contact support.")
        else:
            messages.error(request, "Invalid username or password")
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def freelancer_profile(request, user_id):
    freelancer = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(UserProfile, user=freelancer)
    return render(request, 'freelancer_profile.html', {
        'freelancer': freelancer,
        'profile': profile
    })

@freelancer_required
def edit_profile(request):
    profile = request.user.userprofile
    if request.method == "POST":
        profile.bio = request.POST.get('bio')
        profile.skills = request.POST.get('skills')
        profile.experience = request.POST.get('experience')
        if request.FILES.get('image'):
            profile.image = request.FILES['image']
        profile.save()
        return redirect('freelancer_profile', user_id=request.user.id)
    return render(request, 'edit_profile.html', {'profile': profile})

@client_required
def accept_application(request, app_id):
    app = get_object_or_404(Application, id=app_id)
    if app.job.client != request.user:
        return redirect('employer_dashboard')
    # update application
    app.status = 'accepted'
    app.job.status='in_progress'
    app.save()
    app.job.save()
    contract = Contract.objects.create(application=app,job=app.job,client=request.user,freelancer=app.user,agreed_amount=app.job.budget,deadline= app.job.deadline,status='active')
    return redirect('contract_detail', contract_id=contract.id)

@client_required
def reject_application(request, app_id):
    app = get_object_or_404(Application, id=app_id)
    if app.job.client != request.user:
        return redirect('employer_dashboard')
    app.status = 'rejected'
    app.save()
    return redirect('employer_dashboard')

@login_required
def contract_detail(request, contract_id):
    contract = get_object_or_404(
        Contract,
        Q(id=contract_id) & (Q(client=request.user) | Q(freelancer=request.user))
    )
    tasks = Task.objects.filter(contract=contract)
    payments = Payment.objects.filter(contract=contract)
    # CHECK IF ALL TASKS COMPLETED
    all_tasks_completed = tasks.exists() and not tasks.filter(status__in=['pending', 'active']).exists()
    context = {
        "contract": contract,
        "tasks": tasks,
        "payments": payments,
        "has_tasks": tasks.exists(),
        "all_tasks_completed": all_tasks_completed
    }
    return render(request, "contract_detail.html", context)

@client_required
def add_task(request, contract_id):
    contract = get_object_or_404(
        Contract,
        id=contract_id,
        client=request.user
    )

    if request.method == "POST" and not contract.is_fully_paid:
        title = request.POST.get('title', '').strip()
        if title:
            Task.objects.create(contract=contract, title=title, status='active')

    return redirect('contract_detail', contract_id=contract.id)

@client_required
def delete_task(request, task_id):
    task = get_object_or_404(
        Task,
        id=task_id,
        contract__client=request.user
    )
    if request.method == 'POST' and task.status != 'completed':
        contract_id = task.contract.id
        task.delete()
        return redirect('contract_detail', contract_id=contract_id)
    return redirect('contract_detail', contract_id=task.contract.id)

@freelancer_required
def complete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    contract = task.contract
    # only freelancer of contract can complete
    if contract.freelancer != request.user:
        return redirect('freelancer_dashboard')
    if request.method == 'POST':
        task.status = 'completed'
        task.save()
    return redirect('contract_detail', contract_id=contract.id)

@client_required
def add_payment(request, contract_id):
    contract = get_object_or_404(
        Contract,
        id=contract_id,
        client=request.user
    )
    if request.method == "POST":
        amount = contract.agreed_amount or 0
        amount = Decimal(str(amount))

        Payment.objects.create(
            contract=contract,
            amount=amount,
            status='paid'
        )
        #  CHANGE CONTRACT STATUS
        contract.status = 'completed'
        contract.job.status = 'completed'
        contract.is_fully_paid = True
        contract.save()
        contract.job.save()

        # CHANGE APPLICATION STATUS
        application = Application.objects.filter(
            job=contract.job,
            user=contract.freelancer
        ).first()

        if application:
            application.status = 'completed'
            application.save()

    return redirect('contract_detail', contract_id=contract.id)
@client_required
def edit_task(request, task_id):
    task = get_object_or_404(
        Task,
        id=task_id,
        contract__client=request.user
    )
    if request.method == "POST":
        if task.status != 'completed':
            task.title = request.POST.get('title')
            task.save()
    return redirect('employer_dashboard')

@client_required
def edit_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, client=request.user)
    if request.method == "POST":
        job.title = request.POST.get('title')
        job.description = request.POST.get('description')
        job.deadline = request.POST.get('deadline')
        try:
            budget = int(request.POST.get('budget', 0))
            if budget <= 0:
                raise ValueError
            job.budget = budget
        except (ValueError, TypeError):
            messages.error(request, "Invalid budget")
            return render(request, 'edit_job.html', {'job': job})
        job.save()
        return redirect('employer_dashboard')
    return render(request, 'edit_job.html', {'job': job})

@client_required
def delete_job(request, job_id):
    job = get_object_or_404(Job, id=job_id, client=request.user)
    if request.method == 'POST':
        job.delete()
    return redirect('employer_dashboard')
@login_required
def client_profile(request, user_id):
    client = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(Clientprofile, user=client)
    return render(request, 'client_profile.html', {
        'client': client,
        'profile': profile
    })

@client_required
def edit_client_profile(request):
    profile = get_object_or_404(Clientprofile, user=request.user)
    if request.method == "POST":
        profile.phone = request.POST.get('phone')
        profile.company_name = request.POST.get('company_name')
        profile.save()
        return redirect('client_profile', user_id=request.user.id)
    return render(request, 'edit_client_profile.html', {'profile': profile})

@client_required
def create_payment_order(request, contract_id):
    import razorpay

    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )
    contract = get_object_or_404(Contract, id=contract_id, client=request.user)
    amount = contract.agreed_amount
    if not amount or float(amount) <= 0:
        return JsonResponse({"error": "Invalid amount"}, status=400)
    amount_paise = int(float(amount) * 100)
    order = rzp_client.order.create({
        "amount": amount_paise,
        "currency": "INR",
        "payment_capture": 1
    })

    Payment.objects.create(
        contract=contract,
        amount=amount,
        status='pending',
        razorpay_order_id=order['id']
    )
    return JsonResponse({
        "order_id": order['id'],
        "amount": amount_paise,
        "key": settings.RAZORPAY_KEY_ID
    })
@csrf_exempt
@require_POST
def verify_payment(request):
    import razorpay
    try:
        print("VERIFY VIEW HIT")
        data = json.loads(request.body)
        print("VERIFY DATA:", data)
        rzp_client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )
        razorpay_order_id = data.get("razorpay_order_id")
        razorpay_payment_id = data.get("razorpay_payment_id")
        razorpay_signature = data.get("razorpay_signature")
        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return JsonResponse({"status": "failure", "error": "Missing fields"}, status=400)
        # verify signature
        rzp_client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        })
        payment = Payment.objects.filter(
            razorpay_order_id=razorpay_order_id
        ).first()
        if not payment:
            return JsonResponse({"status": "failure", "error": "Payment not found"}, status=404)

        print("PAYMENT FOUND:", payment.id)
        if payment.status == "paid":
            return JsonResponse({"status": "success", "message": "Already done"})
        payment.status = "paid"
        payment.razorpay_payment_id = razorpay_payment_id
        payment.save()
        contract = payment.contract
        print("CONTRACT BEFORE:", contract.status)
        contract.status = "completed"
        contract.is_fully_paid = True
        contract.save()
        contract.job.status = "completed"
        contract.job.save()
        Application.objects.filter(
            job=contract.job,
            user=contract.freelancer
        ).update(status="completed")
        print("CONTRACT AFTER:", contract.status)
        return JsonResponse({"status": "success"})
    except Exception as e:
        print("VERIFY ERROR:", str(e))
        return JsonResponse({"status": "failure", "error": str(e)})
# Create your views here.
