from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.validators import EMPTY_VALUES
from django.db.models import DateField
from django.db.models.aggregates import Count, Avg
from django.db.models.functions import Cast
from django.utils.timezone import now
from django.utils.translation import ugettext as _
from django.views.generic.list import ListView

from pragmatic.mixins import StaffRequiredMixin

from votebase.core.statistics.mixins import StatisticsFilterMixin


class InfographicsView(StatisticsFilterMixin, ListView):
    template_name = 'statistics/survey_infographics.html'

    def get_statistics(self):
        statistics = {}
        
        if self.filter.is_valid():
            data_voters = self.get_data_voters()
            statistics.update({
                'data_age': self.get_data_age(),
                'data_gender': self.get_data_gender(),
                'data_voters': data_voters,
                'data_voters_total': self.get_data_voters_total(data_voters),
                'data_voting_duration': self.get_data_voting_duration()
            })
            
            if self.survey.is_quiz:
                statistics.update({
                    'data_quiz_result': self.get_data_quiz_result(),
                    'data_quiz_result_by_age': self.get_data_quiz_result_by_age()
                })

        return statistics

    def get_data_quiz_result_by_age(self):
        User = get_user_model()

        if hasattr(User, 'age'):
            return self.get_data_quiz_result_by_age__age_field()

        if hasattr(User, 'date_of_birth'):
            return self.get_data_quiz_result_by_age__dob()

        return []

    def get_data_quiz_result_by_age__age_field(self):
        def calculate(field_path):
            result_path = 'quiz_result'
            my_filter = dict()
            my_filter['%s__isnull' % result_path] = True
            my_filter['%s__isnull' % field_path] = True

            return self.get_queryset()\
                .exclude(user__isnull=True)\
                .exclude(**my_filter)\
                .order_by(field_path)\
                .values(field_path)\
                .annotate(average_result=Avg(result_path))

        field_path = 'user__age'
        voters = calculate(field_path)

        data = []
        try:
            for voter in voters:
                data.append({
                    'age': voter[field_path],
                    'average_result': voter['average_result']
                })
        except ValueError:
            pass
        return data

    def get_data_quiz_result_by_age__dob(self):
        result_path = 'quiz_result'

        def calculate(field_path):
            my_filter = dict()
            my_filter['%s__isnull' % result_path] = True
            my_filter['%s__isnull' % field_path] = True

            return self.get_queryset()\
                .exclude(user__isnull=True)\
                .exclude(**my_filter)\
                .order_by(field_path)\
                .values(field_path, result_path)

        field_path = 'user__date_of_birth'
        voters = calculate(field_path)

        results = dict()
        for voter in voters:
            date = voter[field_path]
            if date in EMPTY_VALUES:
                continue
            age = (now().date() - date).days/365
            quiz_result = voter[result_path]
            if not age in results:
                results[age] = {
                    'count': 1,
                    'sum': quiz_result,
                    'avg': quiz_result
                }
            else:
                old_count = results[age]['count']
                new_count = old_count+1
                old_sum = results[age]['sum']
                new_sum = old_sum + quiz_result
                new_avg = new_sum/new_count
                results[age] = {
                    'count': new_count,
                    'sum': new_sum,
                    'avg': new_avg
                }

        data = []
        try:
            for age in results:
                data.append({
                    'age': age,
                    'average_result': results[age]['avg']
                })
        except ValueError:
            pass

        return data

    def get_data_quiz_result(self):
        field_path = 'quiz_result'
        my_filter = dict()
        my_filter['%s__isnull' % field_path] = True

        voters = self.get_queryset()\
            .exclude(**my_filter)\
            .values(field_path)\
            .annotate(count=Count(field_path))\
            .order_by(field_path)

        data = []

        try:
            for voter in voters:
                data.append({
                    'quiz_result': str(voter[field_path]),
                    'count': voter['count']
                })
        except ValueError:
            pass
        return data

    def get_data_voting_duration(self):
        field_path = 'voting_duration'
        my_filter = dict()
        my_filter['%s__isnull' % field_path] = True

        voters = self.get_queryset()\
            .exclude(**my_filter)\
            .extra(select={field_path: '%s/60' % field_path})\
            .values(field_path)\
            .annotate(count=Count(field_path))\
            .order_by(field_path)

        data = []

        try:
            for voter in voters:
                data.append({
                    'duration': str(voter[field_path]),
                    'count': voter['count']
                })
        except ValueError:
            pass
        return data

    def get_data_voters(self):
        field_name = 'created'
        new_field_name = '{}_date'.format(field_name)

        voters = self.get_queryset() \
            .annotate(**{new_field_name: Cast(field_name, DateField())}) \
            .values(new_field_name)\
            .annotate(count=Count(new_field_name))\
            .order_by(new_field_name)

        data = []
        try:
            for voter in voters:
                data.append({
                    'date': str(voter[new_field_name]),
                    'count': voter['count'],
                })
        except ValueError:
            pass
        return data

    def get_data_voters_total(self, data_voters):
        data = []

        try:
            for d in data_voters:
                created_datetime = datetime.strptime(d['date'], '%Y-%m-%d')+timedelta(days=1)
                count_total = self.get_queryset().filter(created__lte=created_datetime).count()

                data.append({
                    'date': d['date'],
                    'count': count_total,
                })
        except ValueError:
            pass
        return data

    def get_data_gender(self):
        User = get_user_model()

        if not hasattr(User, 'gender'):
            return []

        field_path = 'user__gender'

        genders_registered = self.get_queryset()\
            .values(field_path).annotate(count=Count(field_path))\
            .order_by(field_path)

        genders_anonymous = self.get_queryset().filter(user__isnull=True)

        data = []

        try:
            for gender in genders_registered:
                label_value = gender[field_path]
                count = gender['count']

                if label_value == User.GENDER_MALE:
                    label = _('Male')
                elif label_value == User.GENDER_FEMALE:
                    label = _('Female')
                else:
                    label = _('Unknown')
                    count += genders_anonymous.count()

                data.append({
                    'label': label,
                    'count': count
                })

        except ValueError:
            pass
        return data

    def get_data_age(self):
        User = get_user_model()

        if hasattr(User, 'age'):
            return self.get_data_age_by_age()

        if hasattr(User, 'date_of_birth'):
            return self.get_data_age_by_dob()

        return []

    def get_data_age_by_age(self):
        def calculate(field_path):
            my_filter = dict()
            my_filter['%s__isnull' % field_path] = True

            return self.get_queryset()\
                .exclude(user__isnull=True)\
                .exclude(**my_filter)\
                .values(field_path).annotate(count=Count(field_path))\
                .order_by(field_path)

        field_path = 'user__age'
        ages = calculate(field_path)

        data = []
        try:
            for age in ages:
                data.append({
                    'age': age[field_path],
                    'count': age['count']
                })
        except ValueError:
            pass
        return data

    def get_data_age_by_dob(self):
        dates_of_birth = self.get_queryset()\
            .exclude(user__isnull=True)\
            .exclude(user__profile__date_of_birth__isnull=True)\
            .values_list('user__profile__date_of_birth', flat=True)\
            .order_by('-user__profile__date_of_birth')

        ages = []
        for date_of_birth in dates_of_birth:
            ages.append((now().date() - date_of_birth).days/365)

        data = []
        try:
            age_min = min(ages)
            age_max = max(ages)
            for age in range(max(age_min-10, 0), age_max+10):
                data.append({
                    'age': age,
                    'count': ages.count(age)
                })
        except ValueError:
            pass
        return data
