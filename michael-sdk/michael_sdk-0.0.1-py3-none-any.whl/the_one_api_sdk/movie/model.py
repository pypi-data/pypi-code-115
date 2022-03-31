from the_one_api_sdk.common import BaseModel
from the_one_api_sdk.quote import QuoteApi


class Movie(BaseModel):
    attributes_map = {
        '_id': 'id',
        'name': 'name',
        'runtimeInMinutes': 'runtime_in_minutes',
        'budgetInMillions': 'budget_in_millions',
        'boxOfficeRevenueInMillions': 'box_office_revenue_in_millions',
        'academyAwardNominations': 'academy_award_nominations',
        'academyAwardWins': 'academy_award_wins',
        'rottenTomatoesScore': 'rotten_tomatoes_score',
    }
    id = None
    name = None
    runtime_in_minutes = None
    budget_in_millions = None
    box_office_revenue_in_millions = None
    academy_award_nominations = None
    academy_award_wins = None
    rotten_tomatoes_score = None

    @property
    def quote(self):
        obj = QuoteApi(self.api_client)
        obj.list_path = f'/movie/{self.id}/quote'
        return obj

    def __repr__(self):
        return f'<Movie: {self.id}, {self.name}>'
