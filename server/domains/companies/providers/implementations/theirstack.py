from company_information_service_provider import CompanyInformationServiceProvider


class TheirStackProvider(CompanyInformationServiceProvider):
    @property
    def provider_name(self) -> str:
        return "theirstack"

    def get_company_information(self, name: str) -> dict:
        # Implementation for TheirStack API integration
        pass
