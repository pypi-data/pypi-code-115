from django.utils.translation import ugettext_lazy as _
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from votebase.core.questionnaires.models import Question
from votebase.core.voting.models import Voter


class VoteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        voter_id = request.data.get('voter_id')
        voter = Voter.objects.get(id=voter_id)

        if voter.user != request.user:
            return Response(status=403, data=_("Voter and request user mismatch"))

        if voter.time_limit_expired():
            return Response(status=403, data=_("Time expired"))

        question = Question.objects.get(id=request.data.get('question_id'))

        if question.survey != voter.survey:
            return Response(status=400, data=_("Voter and question survey mismatch"))

        # data
        # radio
        # post_data: {'385-options': '2074'}
        # ic| voting_form.cleaned_data: {'options': '2074'}
        # ic| voting_form.data: {'385-options': '2074'}

        # matrix
        # ic| post_data: {'387-options': '2082',
        #                 '390-matrix_0': '2100',
        #                 '390-matrix_1': '2100',
        #                 '390-matrix_2': '2101',
        #                 '390-matrix_3': '2101',

        # matrix: voting_form.cleaned_data: {'matrix': '2101-2101-2100-2100'}
        # ic| voting_form.cleaned_data: {}
        # ic| voting_form.data: {'390-matrix_2': '2100'}

        voting_form = question.get_voting_form(post_data=request.data.get('post_data'))
        voting_form.full_clean()

        if not voting_form.is_valid():
            return Response(status=200, data=_('Answers not saved because form is not valid'))

        try:
            voting_form.save(voter=voter)
        except:
            return Response(status=400, data=_("Answers couldn't be saved"))

        return Response(status=200, data=_('Answers saved'))
