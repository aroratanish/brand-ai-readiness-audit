from typing import Optional


class MetadataAnalyzer:

    def __init__(
        self,
        title_min_length: int = 10,
        title_max_length: int = 60,
        description_min_length: int = 50,
        description_max_length: int = 160,
    ):

        self.title_min_length = title_min_length
        self.title_max_length = title_max_length

        self.description_min_length = (
            description_min_length
        )

        self.description_max_length = (
            description_max_length
        )

    def analyze(
        self,
        title: Optional[str],
        meta_description: Optional[str],
        h1: list[str],
        h2: list[str],
    ):

        findings = []

        findings.extend(
            self._check_title(title)
        )

        findings.extend(
            self._check_description(
                meta_description
            )
        )

        findings.extend(
            self._check_h1(h1)
        )

        findings.extend(
            self._check_h2(h2)
        )

        return findings

    def _check_title(
        self,
        title: Optional[str]
    ):

        findings = []

        if title is None or not title.strip():

            findings.append(
                {
                    "check": "title",
                    "status": "missing",
                    "evidence": {
                        "value": None
                    }
                }
            )

            return findings

        value = title.strip()

        length = len(value)

        if length < self.title_min_length:

            findings.append(
                {
                    "check": "title",
                    "status": "too_short",
                    "evidence": {
                        "value": value,
                        "length": length,
                        "recommended_range": [
                            self.title_min_length,
                            self.title_max_length,
                        ],
                    },
                }
            )

        elif length > self.title_max_length:

            findings.append(
                {
                    "check": "title",
                    "status": "too_long",
                    "evidence": {
                        "value": value,
                        "length": length,
                        "recommended_range": [
                            self.title_min_length,
                            self.title_max_length,
                        ],
                    },
                }
            )

        else:

            findings.append(
                {
                    "check": "title",
                    "status": "ok",
                    "evidence": {
                        "value": value,
                        "length": length,
                    },
                }
            )

        return findings

    def _check_description(
        self,
        description: Optional[str]
    ):

        findings = []

        if (
            description is None
            or not description.strip()
        ):

            findings.append(
                {
                    "check": "meta_description",
                    "status": "missing",
                    "evidence": {
                        "value": None
                    }
                }
            )

            return findings

        value = description.strip()

        length = len(value)

        if (
            length
            < self.description_min_length
        ):

            findings.append(
                {
                    "check": "meta_description",
                    "status": "too_short",
                    "evidence": {
                        "value": value,
                        "length": length,
                        "recommended_range": [
                            self.description_min_length,
                            self.description_max_length,
                        ],
                    },
                }
            )

        elif (
            length
            > self.description_max_length
        ):

            findings.append(
                {
                    "check": "meta_description",
                    "status": "too_long",
                    "evidence": {
                        "value": value,
                        "length": length,
                        "recommended_range": [
                            self.description_min_length,
                            self.description_max_length,
                        ],
                    },
                }
            )

        else:

            findings.append(
                {
                    "check": "meta_description",
                    "status": "ok",
                    "evidence": {
                        "value": value,
                        "length": length,
                    },
                }
            )

        return findings

    def _check_h1(
        self,
        h1: list[str]
    ):

        if len(h1) == 0:

            return [
                {
                    "check": "h1",
                    "status": "missing",
                    "evidence": {
                        "count": 0,
                        "values": [],
                    },
                }
            ]

        if len(h1) > 1:

            return [
                {
                    "check": "h1",
                    "status": "multiple",
                    "evidence": {
                        "count": len(h1),
                        "values": h1,
                    },
                }
            ]

        return [
            {
                "check": "h1",
                "status": "ok",
                "evidence": {
                    "count": 1,
                    "values": h1,
                },
            }
        ]

    def _check_h2(
        self,
        h2: list[str]
    ):

        return [
            {
                "check": "h2",
                "status": (
                    "present"
                    if h2
                    else "missing"
                ),
                "evidence": {
                    "count": len(h2),
                    "values": h2,
                },
            }
        ]