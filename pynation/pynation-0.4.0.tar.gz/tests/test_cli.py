
import pytest
from pynation.cli import cli1 as cli
from pynation.utils import return_country
from pynation.data import country_calling_code, country_data, currency_data
from click.testing import CliRunner


def test_return_country():
    assert return_country(currency_data, 'united s**') is None
    assert return_country(country_data, 'united states of America') == ('US', 'USA', 840)
    assert return_country(country_calling_code, "United Kingdom")[0] == "44"


class TestCli:

    runner = CliRunner()

    def test_correct_country(self):
        result = self.runner.invoke(cli, ["Somalia"])
        assert result.exit_code == 0
        assert "Information about" in result.output
        assert "Currency Name" in result.output
        assert "SO" in result.output

    def test_wrong_country(self):
        result = self.runner.invoke(cli, ['eeieidjjdl'])
        assert 'Country does not exist' in result.output

    def test_info_correct_country(self):
        result = self.runner.invoke(cli, ['info', 'Nigeria'])
        assert result.exit_code == 0
        assert "Information about" in result.output
        assert "Currency Name" in result.output
        assert 'NG' in result.output

    def test_info_wrong_country(self):
        result = self.runner.invoke(cli, ['info', 'eeieidjjdl'])
        assert 'Country does not exist' in result.output

    def test_short_two_digit(self):
        result = self.runner.invoke(cli, ['short', 'Nigeria'])
        assert result.exit_code == 0
        assert "NGA" not in result.output
        assert 'NG' in result.output
    
    def test_short_three_digit(self):
        result = self.runner.invoke(cli, ['short', 'Nigeria', '-ab=3'])
        assert result.exit_code == 0
        assert "NGA" in result.output
        assert 'NG' not in result.output.split(' ')

        result1 = self.runner.invoke(cli, ['short', 'NIGERIA', '-ab=4'])
        assert 'Error' in result1.output

    def test_currency_nigeria(self):
        result = self.runner.invoke(cli, ['currency', 'nigeria'])
        assert '(₦)' in result.output

    def test_currency_code_option(self):
        result = self.runner.invoke(cli, ['currency', 'NIGERIA', '--code'])
        assert 'NGN' in result.output

    def test_single_calling_code(self):
        result = self.runner.invoke(cli, ['call', 'Afghanistan'])
        assert '93' in result.output

    def test_multiple_calling_code(self):
        result = self.runner.invoke(cli, ['call', 'Puerto Rico'])
        assert '+1-787 or ' in result.output
