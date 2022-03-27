"""cloudfront base URL and path."""
from .responses import CloudFrontResponse

response = CloudFrontResponse()

url_bases = [
    r"https?://cloudfront\.amazonaws\.com",
]

url_paths = {
    "{0}/2020-05-31/distribution$": response.distributions,
    "{0}/2020-05-31/distribution/(?P<distribution_id>[^/]+)$": response.individual_distribution,
}
