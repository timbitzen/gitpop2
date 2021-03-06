import json
from urllib.error import URLError
from urllib.request import urlopen

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from gitpop2.forms import ContactForm, PopForm


def home(request):
    form = PopForm()
    data = {
        "form": form,
    }
    return render(request, "home.html", data)


def pop_form(request):
    if request.method == "POST":  # If the form has been submitted...
        form = PopForm(request.POST)  # A form bound to the POST data
        if form.is_valid():  # All validation rules pass
            # Process the data in form.cleaned_data
            giturl = form.cleaned_data["giturl"]
            giturl = giturl.strip("/")  # removes trailing slash
            owner = giturl.split("/")[-2]
            repo = giturl.split("/")[-1]
            return HttpResponseRedirect(
                reverse("repo_pop", kwargs={"owner": owner, "repo": repo})
            )
    else:
        form = PopForm()
    data = {
        "form": form,
    }
    return render(request, "home.html", data)


def repo_pop(request, owner, repo):
    """
    GET /repos/:owner/:repo/forks
    https://api.github.com/repos/netaustin/redmine_task_board/forks
    """
    src_repo_url = "https://api.github.com/repos/%s/%s" % (owner, repo)
    forks_url = src_repo_url + "/forks?sort=stargazers&per_page=100"
    try:
        src_repo_json = urlopen(src_repo_url)
        forks_json = urlopen(forks_url)
    except URLError:
        raise Http404
    src_repo = json.load(src_repo_json)
    forks = json.load(forks_json)
    repos = forks + [src_repo]
    # sorts src_repo with forks
    repos.sort(key=lambda x: x["stargazers_count"], reverse=True)
    giturl = "https://github.com/%s/%s" % (owner, repo)
    initial = {
        "giturl": giturl,
    }
    form = PopForm(initial=initial)
    data = {
        "repos": repos,
        "form": form,
    }
    return render(request, "detail.html", data)


def contact(request):
    if request.method == "POST":  # If the form has been submitted...
        # ContactForm was defined in the the previous section
        form = ContactForm(request.POST)  # A form bound to the POST data
        if form.is_valid():  # All validation rules pass
            # Process the data in form.cleaned_data
            subject = form.cleaned_data["subject"]
            message = form.cleaned_data["message"]
            sender = form.cleaned_data["sender"]
            cc_myself = form.cleaned_data["cc_myself"]
            recipients = [tup[1] for tup in settings.MANAGERS]
            if cc_myself:
                recipients.append(sender)
            send_mail(subject, message, sender, recipients)
            messages.success(
                request, "Message sent, redirecting to home page."
            )
            return HttpResponseRedirect(reverse("home"))
    else:
        form = ContactForm()

    return render(request, "contact.html", {"form": form})
