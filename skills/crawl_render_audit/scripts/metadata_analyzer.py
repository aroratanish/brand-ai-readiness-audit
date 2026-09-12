class MetadataAnalyzer:
    """
    Deterministic analyzer for page metadata.

    This analyzer reports factual observations only.
    It does not assign severity or recommendations.
    """

    def __init__(
        self,
        title_min=10,
        title_max=60,
        description_min=50,
        description_max=160,
    ):
        self.title_min = title_min
        self.title_max = title_max
        self.description_min = description_min
        self.description_max = description_max

    def _evidence(
        self,
        observed_value,
        source="raw_html",
        confidence="high",
        **extra,
    ):
        evidence = {
            "observed_value": observed_value,
            "source": source,
            "confidence": confidence,
        }

        evidence.update(extra)

        return evidence

    def _check_title(self, title):
        if not title:
            return {
                "check": "title",
                "status": "missing",
                "evidence": self._evidence(
                    observed_value=None,
                ),
            }

        length = len(title)

        if length < self.title_min:
            return {
                "check": "title",
                "status": "too_short",
                "evidence": self._evidence(
                    observed_value=title,
                    observed_length=length,
                    recommended_range={
                        "min": self.title_min,
                        "max": self.title_max,
                    },
                ),
            }

        if length > self.title_max:
            return {
                "check": "title",
                "status": "too_long",
                "evidence": self._evidence(
                    observed_value=title,
                    observed_length=length,
                    recommended_range={
                        "min": self.title_min,
                        "max": self.title_max,
                    },
                ),
            }

        return {
            "check": "title",
            "status": "ok",
            "evidence": self._evidence(
                observed_value=title,
                observed_length=length,
                recommended_range={
                    "min": self.title_min,
                    "max": self.title_max,
                },
            ),
        }

    def _check_description(self, description):
        if not description:
            return {
                "check": "meta_description",
                "status": "missing",
                "evidence": self._evidence(
                    observed_value=None,
                ),
            }

        length = len(description)

        if length < self.description_min:
            return {
                "check": "meta_description",
                "status": "too_short",
                "evidence": self._evidence(
                    observed_value=description,
                    observed_length=length,
                    recommended_range={
                        "min": self.description_min,
                        "max": self.description_max,
                    },
                ),
            }

        if length > self.description_max:
            return {
                "check": "meta_description",
                "status": "too_long",
                "evidence": self._evidence(
                    observed_value=description,
                    observed_length=length,
                    recommended_range={
                        "min": self.description_min,
                        "max": self.description_max,
                    },
                ),
            }

        return {
            "check": "meta_description",
            "status": "ok",
            "evidence": self._evidence(
                observed_value=description,
                observed_length=length,
                recommended_range={
                    "min": self.description_min,
                    "max": self.description_max,
                },
            ),
        }

    def _check_h1(self, h1):
        h1 = h1 or []

        if len(h1) == 0:
            return {
                "check": "h1",
                "status": "missing",
                "evidence": self._evidence(
                    observed_value=[],
                    count=0,
                ),
            }

        if len(h1) > 1:
            return {
                "check": "h1",
                "status": "multiple",
                "evidence": self._evidence(
                    observed_value=h1,
                    count=len(h1),
                ),
            }

        return {
            "check": "h1",
            "status": "ok",
            "evidence": self._evidence(
                observed_value=h1,
                count=1,
            ),
        }

    def _check_h2(self, h2):
        h2 = h2 or []

        if len(h2) == 0:
            return {
                "check": "h2",
                "status": "missing",
                "evidence": self._evidence(
                    observed_value=[],
                    count=0,
                ),
            }

        return {
            "check": "h2",
            "status": "present",
            "evidence": self._evidence(
                observed_value=h2,
                count=len(h2),
            ),
        }

    def analyze(
        self,
        title,
        description,
        h1,
        h2,
    ):
        return [
            self._check_title(title),
            self._check_description(description),
            self._check_h1(h1),
            self._check_h2(h2),
        ]