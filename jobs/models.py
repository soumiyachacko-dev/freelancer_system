from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Job(models.Model):
    title = models.CharField(max_length=200)
    client = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    budget = models.IntegerField()
    status = models.CharField(
        max_length=20,
        choices=[
            ('open', 'Open'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed')
        ],
        default='open'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    deadline = models.DateField(null=True, blank=True)
    def __str__(self):
        return self.title

class Application(models.Model):
    class Meta:
        unique_together = ['user', 'job']
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('rejected', 'Rejected'),
            ('completed', 'Completed')
        ],
        default='pending'
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user.username} → {self.job.title}"

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('client', 'Client'),
        ('freelancer', 'Freelancer'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    bio = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='profiles/', default='default.png', blank=True)
    skills = models.CharField(max_length=255, blank=True, null=True)
    experience = models.TextField(blank=True, null=True)
    def __str__(self):
        return f"{self.user.username} ({self.role})"


class Contract(models.Model):
    application = models.OneToOneField(
        Application,
        on_delete=models.CASCADE,
        related_name='contract'
    )

    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='client_contracts'
    )
    freelancer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='freelancer_contracts'
    )
    agreed_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('inactive', 'Inactive'),
            ('active', 'Active'),
            ('completed', 'Completed')
        ],
        default='inactive'
    )

    start_date = models.DateTimeField(auto_now_add=True)
    is_fully_paid = models.BooleanField(default=False)

    @property
    def is_started(self):
        return self.tasks.exists()

    @property
    def is_active(self):
        return self.tasks.exists() and not self.is_fully_paid

    @property
    def is_completed(self):
        return self.is_fully_paid

class Task(models.Model):
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    title = models.CharField(max_length=200)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending','Pending'),
            ('active', 'Active'),
            ('completed','Completed')
        ],
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.title

class Payment(models.Model):
    contract = models.ForeignKey(Contract, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('paid', 'Paid')
        ],
        default='pending'
    )
    razorpay_order_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_payment_id = models.CharField(max_length=255, null=True, blank=True)
    razorpay_signature = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
class Clientprofile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    company_name = models.CharField(max_length=50, blank=True)
    def __str__(self):
        return f"{self.user.username} ({self.company_name})"


# Create your models here.
