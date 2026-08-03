from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from agency.models import Topic, Newspaper, Redactor


class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = "__all__"


class NewspaperForm(forms.ModelForm):
    publishers = forms.ModelMultipleChoiceField(
        queryset=Redactor.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="An issue with no editor lands in the unassigned queue.",
    )

    class Meta:
        model = Newspaper
        fields = ["title", "publish_date", "topics", "publishers", "content"]
        widgets = {
            "publish_date": forms.DateInput(attrs={"type": "date"}),
            "topics": forms.CheckboxSelectMultiple,
        }


class RedactorCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Redactor
        fields = UserCreationForm.Meta.fields + (
            "first_name",
            "last_name",
            "email",
            "years_of_experience",
        )


class RedactorUpdateForm(UserChangeForm):
    password = None

    class Meta:
        model = Redactor
        fields = ["username", "first_name", "last_name", "email", "years_of_experience"]


class RedactorExperienceForm(forms.ModelForm):
    class Meta:
        model = Redactor
        fields = ["years_of_experience"]


class SearchForm(forms.Form):
    query = forms.CharField(
        max_length=255,
        required=False,
        label="",
        widget=forms.TextInput(
            attrs={
                "placeholder": "Search",
                "class": "form-control",
            }
        ),
    )
