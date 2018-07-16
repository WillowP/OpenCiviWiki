import json

from django.conf import settings
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.db.models import F
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse

from api.models import Category, Account, Thread, Civi, Activity, Invitation
from api.forms import UpdateProfileImage
from api.serializers import AccountListSerializer
from utils.constants import US_STATES
from utils.custom_decorators import login_required, full_account


def base_view(request):
    if not request.user.is_authenticated():
        return TemplateResponse(request, 'static_templates/landing.html', {})

    request_account = Account.objects.get(user=request.user)
    if not request_account.full_account:
        return HttpResponseRedirect('/setup')

    context = {
        'username': request.user.username,
        'google_map_api_key': settings.GOOGLE_API_KEY
    }
    return TemplateResponse(request, 'app.html', context)


@login_required
@full_account
def user_profile(request, username=None):
    if not username:
        return HttpResponseRedirect('/profile/{0}'.format(request.user))
    else:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return HttpResponseRedirect('/404')
    context = {
        'username': request.user.username,
        'google_map_api_key': settings.GOOGLE_API_KEY,
    }
    return TemplateResponse(request, 'app.html', context)

@login_required
def user_setup(request):
    account = Account.objects.get(user=request.user)
    if account.full_account:
        return HttpResponseRedirect('/')

    context = {
        'username': request.user.username,
        'google_map_api_key': settings.GOOGLE_API_KEY
    }
    return TemplateResponse(request, 'app.html', context)



@login_required
@full_account
def issue_thread(request, thread_id=None):
    if not thread_id:
        return HttpResponseRedirect('/404')

    thread = Thread.objects.get(id=thread_id)

    thread.num_views = F('num_views') + 1
    thread.save()

    context = {
        'username': request.user.username,
        'google_map_api_key': settings.GOOGLE_API_KEY
    }
    return TemplateResponse(request, 'app.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def invite(request):
    user = User.objects.get(username=request.user.username)

    invitations = Invitation.objects.filter_by_host(host_user=user).order_by("-date_created").all()
    invitees = [invitation.summarize() for invitation in invitations]
    # response_data = {
    #     'invitees': 
    # }

    # return TemplateResponse(request, 'invite.html', response_data)

    context = {
        'username': request.user.username,
        'google_map_api_key': settings.GOOGLE_API_KEY,
        'data': json.dumps(invitees)
    }
    return TemplateResponse(request, 'app.html', context)


@login_required
def settings_view(request):
    context = {
        'username': request.user.username,
        'google_map_api_key': settings.GOOGLE_API_KEY
    }
    return TemplateResponse(request, 'app.html', context)


def login_view(request):
    if request.user.is_authenticated():
        if request.user.is_active:
            return HttpResponseRedirect('/')

    return TemplateResponse(request, 'app.html', {})


def declaration(request):
    return TemplateResponse(request, 'declaration.html', {})

def landing_view(request):
    return TemplateResponse(request, 'static_templates/landing.html', {})

def how_it_works_view(request):
    return TemplateResponse(request, 'static_templates/how_it_works.html', {})

def about_view(request):
    return TemplateResponse(request, 'static_templates/about.html', {})

def support_us_view(request):
    return TemplateResponse(request, 'static_templates/support_us.html', {})

""" CSV export function. Thread ID goes in, CSV HTTP response attachment goes out. """
@csrf_exempt
def civi2csv(request, thread_id):
    import csv
    thread = thread_id
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment, filename=' + thread + '.csv'
    writer = csv.writer(response, delimiter=',')
    for card in Civi.objects.filter(thread_id=thread):
        data = []
        for key, value in card.dict_with_score().items():
            if value != []:
                data.append(value)
        writer.writerow(data)
    return response
