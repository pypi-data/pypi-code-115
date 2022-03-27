from django.db.models import Count
from django.template.loader import get_template


class StatsManager(object):
    template_name = None

    def __init__(self, question, voters):
        self.question = question
        self.survey = self.question.survey
        self.all_answers = self.question.answer_set.filter(voter__in=voters)
        self.total_answers_count = self.all_answers.count()
        # find maximum answers per option
        # max_answers_per_option = self.all_answers.values('option').annotate(count=Count('option__pk')).order_by('-count')[0]['count']
        self.calc()
        
    def calc(self):
        raise NotImplementedError()

    @property
    def data(self):
        raise NotImplementedError()

    def render(self):
        template = get_template(self.template_name)
        return template.render(self.data)


class OptionsStatsManager(StatsManager):
    template_name = 'statistics/graphs/options.html'

    def calc(self):
        # set option information
        self.max_percent = 0
        self.options = []
        for option in self.question.option_set.all():
            answers = self.all_answers.filter(option=option)
            count = answers.count()

            try:
#                percent = count * 100 / max_answers_per_option
                percent = count * 100 / self.total_answers_count
            except ZeroDivisionError:
                percent = 0
            percent = round(percent, 2)

            if percent > self.max_percent:
                self.max_percent = percent

            self.options.append({
                'is_correct': option.is_correct,
                'title': option.title_i18n,
                'count': answers.count(),
                'percent': percent
            })

    @property
    def data(self):
        # TODO: cache
        return {
            'question': self.question,
            'options': self.options,
            'max_percent': self.max_percent,
            'total_answers': self.total_answers_count,
        }


class TextStatsManager(StatsManager):
    template_name = 'statistics/graphs/options.html'

    def calc(self):
        # order by count
        answers = self.all_answers.values('custom').annotate(count=Count('pk')).order_by('-count')

        # find most repeating custom answer
        # most_custom = answers[0]
        # max_count = most_custom['count']

        # set option information
        self.max_percent = 0
        self.customs = []
        for answer in answers:
            count = answer['count']

            try:
                # percent = count * 100 / max_count
                percent = float(count) * 100 / self.total_answers_count
            except ZeroDivisionError:
                percent = 0
            percent = round(percent, 2)

            if percent > self.max_percent:
                self.max_percent = percent

            self.customs.append({
                'title': answer['custom'],
                'count': count,
                'percent': percent,
            })

    @property
    def data(self):
        return {
            'question': self.question,
            'options': self.customs,
            'max_percent': self.max_percent,
            'total_answers': self.total_answers_count,
        }


class MatrixStatsManager(StatsManager):
    template_name = 'statistics/graphs/matrix.html'

    def calc(self):
        # set row information
        self.options_rows = self.question.option_set.all().rows()
        self.options_columns = self.question.option_set.all().columns()

        self.rows = []
        self.max_percent = 0
        for option_row in self.options_rows:
            columns = []

            for option_column in self.options_columns:
                answers = self.all_answers.filter(option=option_row, option_column=option_column)
                count = answers.count()

                try:
                    # percent = count * 100 / max_answers_per_option
                    percent = count * 100 / self.total_answers_count
                except ZeroDivisionError:
                    percent = 0

                if percent > self.max_percent:
                    self.max_percent = percent

                columns.append({
                    'count': answers.count(),
                    'percent': percent,
                    'is_correct': option_column.is_correct,
                })

            self.rows.append({
                'title': option_row.title_i18n,
                'is_correct': option_row.is_correct,
                'columns': columns
            })

    @property
    def data(self):
        return {
            'question': self.question,
            'rows': self.rows,
            'columns': self.options_columns,
            'max_percent': self.max_percent,
            'total_answers': self.total_answers_count,
        }
