# -*-coding:utf-8-*-

import logging

from django import forms
from django.conf import settings
from django.contrib.auth.models import User

from bot.models import EngagementRule


log = logging.getLogger(settings.PROJECT_NAME+".*")
log.setLevel(settings.DEBUG)

class UserForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):
        super(UserForm, self).__init__(*args,**kwargs)
        self.fields['pass2'].widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Repeat Passowrd'})

    pass2 = forms.CharField(max_length=30, required=True, label="Password" )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'password', 'pass2')

        widgets = {
            'password': forms.PasswordInput(attrs={'placeholder': 'Passowrd'}),
            'pass2': forms.PasswordInput(attrs={'placeholder': 'Repeat Passowrd',}),
        }


class EngagementRuleForm(forms.Form):

    # def __init__(self, configs = None, *args, **kwargs):
    #     super(TradeConfigForm, self).__init__(*args, **kwargs)
    #     if configs:
    #         self.fields['order_type'].initial =

    YES = True; NO = False;
    YES_NO = [(YES, 'Yes'), (NO, "No")]

    READONLY = "Readonly"; BAN = "Ban"; KICK = "Kick";
    ACTION = [(READONLY, 'Readonly'), (KICK, "Kick")]
    # ACTION = [(READONLY, 'Readonly'), (BAN, "Ban"), (KICK, "Kick")]

    text_is_allowed = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'data-type': "text-allow", 'data-toggle': "toggle", 'data-on': "Allow", 'data-off': "Banned", 'data-onstyle': "success", 'data-offstyle': "danger"}))
    text_keywords = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Semi-column (;) separated list of keywords', "style": "width: 100%"}))
    text_regex = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Semi-column (;) separated list of keywords', "style": "width: 100%"}))
    text_delete_forbidden = forms.BooleanField(required=False, widget=forms.CheckboxInput)
    text_is_rate_limited = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"data-type": "text-is-rate-limited", "data-toggle": "toggle", "data-on": "Rate Limiting", "data-off": "Rate Unlimited", "data-onstyle": "success", "data-offstyle": "danger"}))
    text_rate_counter = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', "style": "width: 60px"}))
    text_rate_interval = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', "style": "width: 80px"}))
    text_action_allowed = forms.ChoiceField(required=False, initial=KICK, choices=ACTION, widget=forms.Select(attrs={'class': 'form-control col-md-3', 'style': 'width: 150px'}))
    text_limit_time_allowed = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}))
    text_can_delete = forms.BooleanField(required=False, widget=forms.CheckboxInput)
    text_action_banned = forms.ChoiceField(required=False, initial=KICK, choices=ACTION, widget=forms.Select(attrs={'class': 'form-control col-md-3', 'style': 'width: 150px'}))
    text_limit_time_banned = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}))

    photo_is_allowed = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'data-type':"photo-allow", 'data-toggle': "toggle", 'data-on': "Allow", 'data-off': "Banned", 'data-onstyle': "success", 'data-offstyle': "danger"}))
    photo_is_rate_limited = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"data-type": "photo-is-rate-limited", "data-toggle": "toggle", "data-on": "Rate Limiting", "data-off": "Rate Unlimited", "data-onstyle": "success", "data-offstyle": "danger"}))
    photo_rate_counter = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', "style": "width: 60px"}))
    photo_rate_interval = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', "style": "width: 80px"}))
    photo_action_allowed = forms.ChoiceField(required=False, initial=KICK, choices=ACTION, widget=forms.Select(attrs={'class': 'form-control col-md-3', 'style': 'width: 150px'}))
    photo_limit_time_allowed = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}))
    photo_can_delete = forms.BooleanField(required=False, widget=forms.CheckboxInput)
    photo_action_banned = forms.ChoiceField(required=False, initial=KICK, choices=ACTION, widget=forms.Select(attrs={'class': 'form-control col-md-3', 'style': 'width: 150px'}))
    photo_limit_time_banned = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}))

    audio_is_allowed = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'data-type':"audio-allow", 'data-toggle': "toggle", 'data-on': "Allow", 'data-off': "Banned", 'data-onstyle': "success", 'data-offstyle': "danger"}))
    audio_is_rate_limited = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"data-type": "audio-is-rate-limited", "data-toggle": "toggle", "data-on": "Rate Limiting", "data-off": "Rate Unlimited", "data-onstyle": "success", "data-offstyle": "danger"}))
    audio_rate_counter = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', "style": "width: 60px"}))
    audio_rate_interval = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', "style": "width: 80px"}))
    audio_action_allowed = forms.ChoiceField(required=False, initial=KICK, choices=ACTION, widget=forms.Select(attrs={'class': 'form-control col-md-3', 'style': 'width: 150px'}))
    audio_limit_time_allowed = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}))
    audio_can_delete = forms.BooleanField(required=False, widget=forms.CheckboxInput)
    audio_action_banned = forms.ChoiceField(required=False, initial=KICK, choices=ACTION, widget=forms.Select(attrs={'class': 'form-control col-md-3', 'style': 'width: 150px'}))
    audio_limit_time_banned = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}))

    video_is_allowed = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'data-type':"video-allow", 'data-toggle': "toggle", 'data-on': "Allow", 'data-off': "Banned", 'data-onstyle': "success", 'data-offstyle': "danger"}))
    video_is_rate_limited = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"data-type": "video-is-rate-limited", "data-toggle": "toggle", "data-on": "Rate Limiting", "data-off": "Rate Unlimited", "data-onstyle": "success", "data-offstyle": "danger"}))
    video_rate_counter = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', "style": "width: 60px"}))
    video_rate_interval = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', "style": "width: 80px"}))
    video_action_allowed = forms.ChoiceField(required=False, initial=KICK, choices=ACTION, widget=forms.Select(attrs={'class': 'form-control col-md-3', 'style': 'width: 150px'}))
    video_limit_time_allowed = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}))
    video_can_delete = forms.BooleanField(required=False, widget=forms.CheckboxInput)
    video_action_banned = forms.ChoiceField(required=False, initial=KICK, choices=ACTION, widget=forms.Select(attrs={'class': 'form-control col-md-3', 'style': 'width: 150px'}))
    video_limit_time_banned = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}))

    others_is_allowed = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'data-type':"others-allow", 'data-toggle': "toggle", 'data-on': "Allow", 'data-off': "Banned", 'data-onstyle': "success", 'data-offstyle': "danger"}))
    others_is_rate_limited = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={"data-type": "others-is-rate-limited", "data-toggle": "toggle", "data-on": "Rate Limiting", "data-off": "Rate Unlimited", "data-onstyle": "success", "data-offstyle": "danger"}))
    others_rate_counter = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', "style": "width: 60px"}))
    others_rate_interval = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0', "style": "width: 80px"}))
    others_action_allowed = forms.ChoiceField(required=False, initial=KICK, choices=ACTION, widget=forms.Select(attrs={'class': 'form-control col-md-3', 'style': 'width: 150px'}))
    others_limit_time_allowed = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}))
    others_can_delete = forms.BooleanField(required=False, widget=forms.CheckboxInput)
    others_action_banned = forms.ChoiceField(required=False, initial=KICK, choices=ACTION, widget=forms.Select(attrs={'class': 'form-control col-md-3', 'style': 'width: 150px'}))
    others_limit_time_banned = forms.IntegerField(required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '0'}))

    def clean(self):
        # cleaned_data = super(EngagementRuleForm, self).clean()
        cleaned_data = self.cleaned_data
        if cleaned_data.get('text_is_allowed'):
            if cleaned_data.get('text_is_rate_limited'):
                if cleaned_data.get('text_rate_counter') is None or cleaned_data.get('text_rate_counter') < 2:
                    raise forms.ValidationError('Text: Rate is required')
                if cleaned_data.get('text_rate_interval') is None or cleaned_data.get('text_rate_interval') < 1:
                    raise forms.ValidationError('Text: Rate Interval is required')
            if cleaned_data.get('text_is_rate_limited') or len(cleaned_data.get('text_keywords').strip()) > 0 or len(cleaned_data.get('text_regex').strip()) > 0:
                if cleaned_data.get('text_action_allowed') in [self.READONLY, self.BAN]:
                    if cleaned_data.get('text_limit_time_allowed') is None or cleaned_data.get('text_limit_time_allowed') < 1:
                        raise forms.ValidationError('Text: How long would you like set "{}" for failing the Rate limit/Blacklisted Keywords/Regex?'.format(cleaned_data.get('text_action_allowed')))
        else:
            if cleaned_data.get('text_action_banned') in [self.READONLY, self.BAN]:
                if cleaned_data.get('text_limit_time_banned') is None or cleaned_data.get('text_limit_time_banned') < 1:
                    raise forms.ValidationError('Text: How long would you like set "{}" for failing the Rate limit?'.format(cleaned_data.get('text_action_banned')))

        if cleaned_data.get('photo_is_allowed'):
            if cleaned_data.get('photo_is_rate_limited'):
                if cleaned_data.get('photo_rate_counter') is None or cleaned_data.get('photo_rate_counter') < 2:
                    raise forms.ValidationError('Photo: Rate is required')
                    # self.add_error('photo_rate_counter', 'Photo: Rate is required')
                    # self.add_error('photo_rate_counter', forms.ValidationError('Event end date should not occur before start date.'))
                if cleaned_data.get('photo_rate_interval') is None or cleaned_data.get('photo_rate_interval') < 1:
                    raise forms.ValidationError('Photo: Rate Interval is required')
                if cleaned_data.get('photo_action_allowed') in [self.READONLY, self.BAN]:
                    if cleaned_data.get('photo_limit_time_allowed') is None or cleaned_data.get('photo_limit_time_allowed') < 1:
                        raise forms.ValidationError('Photo: How long would you like set "{}" for failing the Rate limit?'.format(cleaned_data.get('photo_action_allowed')))
        else:
            if cleaned_data.get('photo_action_banned') in [self.READONLY, self.BAN]:
                if cleaned_data.get('photo_limit_time_banned') is None or cleaned_data.get('photo_limit_time_banned') < 1:
                    raise forms.ValidationError('Photo: How long would you like set "{}" for failing the Rate limit?'.format(cleaned_data.get('photo_action_banned')))

        if cleaned_data.get('audio_is_allowed'):
            if cleaned_data.get('audio_is_rate_limited'):
                if cleaned_data.get('audio_rate_counter') is None or cleaned_data.get('audio_rate_counter') < 2:
                    raise forms.ValidationError('Audio: Rate is required')
                    # self.add_error('audio_rate_counter', 'Audio: Rate is required')
                    # self.add_error('audio_rate_counter', forms.ValidationError('Event end date should not occur before start date.'))
                if cleaned_data.get('audio_rate_interval') is None or cleaned_data.get('audio_rate_interval') < 1:
                    raise forms.ValidationError('Audio: Rate Interval is required')
                if cleaned_data.get('audio_action_allowed') in [self.READONLY, self.BAN]:
                    if cleaned_data.get('audio_limit_time_allowed') is None or cleaned_data.get('audio_limit_time_allowed') < 1:
                        raise forms.ValidationError('Audio: How long would you like set "{}" for failing the Rate limit?'.format(cleaned_data.get('audio_action_allowed')))
        else:
            if cleaned_data.get('audio_action_banned') in [self.READONLY, self.BAN]:
                if cleaned_data.get('audio_limit_time_banned') is None or cleaned_data.get('audio_limit_time_banned') < 1:
                    raise forms.ValidationError('Audio: How long would you like set "{}" for failing the Rate limit?'.format(cleaned_data.get('audio_action_banned')))

        if cleaned_data.get('video_is_allowed'):
            if cleaned_data.get('video_is_rate_limited'):
                if cleaned_data.get('video_rate_counter') is None or cleaned_data.get('video_rate_counter') < 2:
                    raise forms.ValidationError('Video: Rate is required')
                    # self.add_error('video_rate_counter', 'Video: Rate is required')
                    # self.add_error('video_rate_counter', forms.ValidationError('Event end date should not occur before start date.'))
                if cleaned_data.get('video_rate_interval') is None or cleaned_data.get('video_rate_interval') < 1:
                    raise forms.ValidationError('Video: Rate Interval is required')
                if cleaned_data.get('video_action_allowed') in [self.READONLY, self.BAN]:
                    if cleaned_data.get('video_limit_time_allowed') is None or cleaned_data.get('video_limit_time_allowed') < 1:
                        raise forms.ValidationError('Video: How long would you like set "{}" for failing the Rate limit?'.format(cleaned_data.get('video_action_allowed')))
        else:
            if cleaned_data.get('video_action_banned') in [self.READONLY, self.BAN]:
                if cleaned_data.get('video_limit_time_banned') is None or cleaned_data.get('video_limit_time_banned') < 1:
                    raise forms.ValidationError('Video: How long would you like set "{}" for failing the Rate limit?'.format(cleaned_data.get('video_action_banned')))

        if cleaned_data.get('others_is_allowed'):
            if cleaned_data.get('others_is_rate_limited'):
                if cleaned_data.get('others_rate_counter') is None or cleaned_data.get('others_rate_counter') < 2:
                    raise forms.ValidationError('Others: Rate is required')
                    # self.add_error('others_rate_counter', 'Others: Rate is required')
                    # self.add_error('others_rate_counter', forms.ValidationError('Event end date should not occur before start date.'))
                if cleaned_data.get('others_rate_interval') is None or cleaned_data.get('others_rate_interval') < 1:
                    raise forms.ValidationError('Others: Rate Interval is required')
                if cleaned_data.get('others_action_allowed') in [self.READONLY, self.BAN]:
                    if cleaned_data.get('others_limit_time_allowed') is None or cleaned_data.get('others_limit_time_allowed') < 1:
                        raise forms.ValidationError('Others: How long would you like set "{}" for failing the Rate limit?'.format(cleaned_data.get('others_action_allowed')))
        else:
            if cleaned_data.get('others_action_banned') in [self.READONLY, self.BAN]:
                if cleaned_data.get('others_limit_time_banned') is None or cleaned_data.get('others_limit_time_banned') < 1:
                    raise forms.ValidationError('Others: How long would you like set "{}" for failing the Rate limit?'.format(cleaned_data.get('others_action_banned')))

        return cleaned_data