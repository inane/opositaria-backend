class ConfigurationError(Exception):
    @classmethod
    def missing(cls, setting_name: str) -> "ConfigurationError":
        return cls(f"{setting_name} is not configured")
