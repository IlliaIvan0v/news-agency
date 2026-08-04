from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import PasswordChangeView
from django.db.models import Count, Max
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views import generic

from agency.forms import (
    NewspaperForm,
    RedactorCreationForm,
    RedactorExperienceForm,
    RedactorUpdateForm,
    SearchForm,
    TopicForm,
)
from agency.models import Newspaper, Topic


class NavTopicsMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nav_topics"] = Topic.objects.all()[:6]
        return context


class SuperuserRequiredMixin(UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        return self.request.user.is_superuser


class SelfOrSuperuserRequiredMixin(UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        obj = self.get_object()

        return self.request.user.is_superuser or obj.pk == self.request.user.pk


class NewspaperOwnerOrSuperuserRequiredMixin(UserPassesTestMixin):
    raise_exception = True

    def test_func(self):
        newspaper = self.get_object()

        return (
            self.request.user.is_superuser
            or newspaper.publishers.filter(pk=self.request.user.pk).exists()
        )


class IndexView(
    LoginRequiredMixin,
    NavTopicsMixin,
    generic.TemplateView,
):
    template_name = "agency/index.html"

    def get_context_data(self, **kwargs):
        return super().get_context_data(**kwargs) | {
            "today": timezone.now(),
            "num_newspapers": Newspaper.objects.count(),
            "num_topics": Topic.objects.count(),
            "num_redactors": get_user_model().objects.count(),
            "num_unassigned": Newspaper.objects.filter(publishers__isnull=True).count(),
            "latest_newspapers": (
                Newspaper.objects.prefetch_related(
                    "topics",
                    "publishers",
                )[:5]
            ),
        }


class SignUpView(generic.CreateView):
    form_class = RedactorCreationForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("agency:index")

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        return response


class SearchListView(
    LoginRequiredMixin,
    generic.ListView,
):
    search_field = ""

    def get_queryset(self):
        queryset = super().get_queryset()
        self.search_form = SearchForm(self.request.GET)

        if self.search_form.is_valid():
            query = self.search_form.cleaned_data["query"]

            if query:
                queryset = queryset.filter(
                    **{
                        f"{self.search_field}__icontains": query,
                    }
                )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_form"] = self.search_form
        context["search_query"] = self.request.GET.get(
            "query",
            "",
        )
        return context


class RedactorPasswordChangeView(
    LoginRequiredMixin,
    NavTopicsMixin,
    PasswordChangeView,
):
    template_name = "registration/password_change_form.html"

    def get_success_url(self):
        return reverse(
            "agency:redactor-detail",
            kwargs={
                "pk": self.request.user.pk,
            },
        )


class TopicListView(
    NavTopicsMixin,
    SearchListView,
):
    model = Topic
    search_field = "name"
    template_name = "agency/topic_list.html"
    paginate_by = 6

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                newspaper_count=Count(
                    "newspapers",
                    distinct=True,
                ),
                last_published=Max("newspapers__publish_date"),
            )
            .order_by("name")
        )


class TopicCreateView(
    LoginRequiredMixin,
    SuperuserRequiredMixin,
    NavTopicsMixin,
    generic.CreateView,
):
    model = Topic
    form_class = TopicForm
    success_url = reverse_lazy("agency:topic-list")


class TopicUpdateView(
    LoginRequiredMixin,
    SuperuserRequiredMixin,
    NavTopicsMixin,
    generic.UpdateView,
):
    model = Topic
    form_class = TopicForm
    success_url = reverse_lazy("agency:topic-list")


class TopicDeleteView(
    LoginRequiredMixin,
    SuperuserRequiredMixin,
    NavTopicsMixin,
    generic.DeleteView,
):
    model = Topic
    success_url = reverse_lazy("agency:topic-list")


class NewspaperListView(
    NavTopicsMixin,
    SearchListView,
):
    model = Newspaper
    template_name = "agency/newspaper_list.html"
    search_field = "title"
    queryset = Newspaper.objects.prefetch_related(
        "topics",
        "publishers",
    )
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        if title := self.request.GET.get("title"):
            queryset = queryset.filter(title__icontains=title)

        if topic_ids := self.request.GET.getlist("topic"):
            queryset = queryset.filter(topics__id__in=topic_ids)

        if self.request.GET.get("unassigned"):
            queryset = queryset.filter(publishers__isnull=True)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        params = self.request.GET.copy()
        params.pop("page", None)

        context["section"] = "newspapers"
        context["selected_topic_ids"] = self.request.GET.getlist("topic")
        context["query_string"] = params.urlencode()

        return context


class NewspaperCreateView(
    LoginRequiredMixin,
    NavTopicsMixin,
    generic.CreateView,
):
    model = Newspaper
    form_class = NewspaperForm
    template_name = "agency/newspaper_form.html"
    success_url = reverse_lazy("agency:newspaper-list")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        if not self.request.user.is_superuser:
            form.fields.pop("publishers", None)

        return form

    def form_valid(self, form):
        response = super().form_valid(form)

        if not self.request.user.is_superuser:
            self.object.publishers.add(self.request.user)

        return response


class NewspaperUpdateView(
    LoginRequiredMixin,
    NewspaperOwnerOrSuperuserRequiredMixin,
    NavTopicsMixin,
    generic.UpdateView,
):
    model = Newspaper
    form_class = NewspaperForm


class NewspaperDeleteView(
    LoginRequiredMixin,
    NewspaperOwnerOrSuperuserRequiredMixin,
    NavTopicsMixin,
    generic.DeleteView,
):
    model = Newspaper
    success_url = reverse_lazy("agency:newspaper-list")


class NewspaperDetailView(
    LoginRequiredMixin,
    NavTopicsMixin,
    generic.DetailView,
):
    model = Newspaper
    template_name = "agency/newspaper_detail.html"


class RedactorListView(
    NavTopicsMixin,
    SearchListView,
):
    model = get_user_model()
    template_name = "agency/redactor_list.html"
    search_field = "username"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                newspaper_count=Count(
                    "newspapers",
                    distinct=True,
                )
            )
        )


class RedactorDetailView(
    LoginRequiredMixin,
    NavTopicsMixin,
    generic.DetailView,
):
    model = get_user_model()
    template_name = "agency/redactor_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["newspapers"] = self.object.newspapers.prefetch_related(
            "topics",
            "publishers",
        )
        return context


class RedactorCreateView(
    LoginRequiredMixin,
    SuperuserRequiredMixin,
    NavTopicsMixin,
    generic.CreateView,
):
    model = get_user_model()
    form_class = RedactorCreationForm
    template_name = "agency/redactor_form.html"


class RedactorUpdateView(
    LoginRequiredMixin,
    SelfOrSuperuserRequiredMixin,
    NavTopicsMixin,
    generic.UpdateView,
):
    model = get_user_model()
    form_class = RedactorUpdateForm


class RedactorUpdateExperienceView(
    LoginRequiredMixin,
    SelfOrSuperuserRequiredMixin,
    NavTopicsMixin,
    generic.UpdateView,
):
    model = get_user_model()
    form_class = RedactorExperienceForm


class RedactorDeleteView(
    LoginRequiredMixin,
    NavTopicsMixin,
    generic.DeleteView,
):
    model = get_user_model()
    success_url = reverse_lazy("agency:redactor-list")
