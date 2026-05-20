from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),

    # dashboards
    path('employer_dashboard/', views.employer_dashboard, name='employer_dashboard'),
    path('freelancer_dashboard/', views.freelancer_dashboard, name='freelancer_dashboard'),

    # jobs
    path('post-job/', views.post_job, name='post_job'),
    path('apply/<int:job_id>/', views.apply_job, name='apply_job'),
    path('job/edit/<int:job_id>/', views.edit_job, name='edit_job'),
    path('job/delete/<int:job_id>/', views.delete_job, name='delete_job'),
    # applications
    path('accept/<int:app_id>/', views.accept_application, name='accept_application'),
    path('reject/<int:app_id>/', views.reject_application, name='reject_application'),

    # contracts (project)
    path('contract/<int:contract_id>/', views.contract_detail, name='contract_detail'),

    # tasks
    path('task/add/<int:contract_id>/', views.add_task, name='add_task'),
    path('task/complete/<int:task_id>/', views.complete_task, name='complete_task'),
    path('task/edit/<int:task_id>/', views.edit_task, name='edit_task'),
    path('task/delete/<int:task_id>/', views.delete_task, name='delete_task'),
    # payments
    path('payment/add/<int:contract_id>/', views.add_payment, name='add_payment'),
    path('create-payment-order/<int:contract_id>/', views.create_payment_order, name='create_payment_order'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    # user
    path('my-applications/', views.my_applications, name='my_applications'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # profile
    path('freelancer/<int:user_id>/', views.freelancer_profile, name='freelancer_profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('client/<int:user_id>/', views.client_profile, name='client_profile'),
    path('edit-client_profile/', views.edit_client_profile, name='edit_client_profile'),

    path('forgot-password/', auth_views.PasswordResetView.as_view(
        template_name='forgot_password.html'
    ), name='forgot_password'),
    path('forgot-password/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='forgot_password_done.html'
    ), name='password_reset_done'),

    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='reset_password_confirm.html'
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='reset_password_done.html'
    ), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)